"""Owner-scoped, local-first object storage for AM Projects (G14).

Design laws:
  * Bytes are written to a runtime data root OUTSIDE the public web directory.
  * Object keys are opaque, server-generated hex — never a client-controlled path.
    Path traversal, symlink escape and absolute-path injection are impossible by
    construction: the client never supplies any path component.
  * Writes are atomic (temp file + os.replace) with restrictive permissions.
  * SHA-256 and byte length are computed while streaming and re-verified from disk.
  * Uploads are size-capped by streaming, never by trusting a declared length.
  * Nothing here executes uploaded content; dangerous formats are quarantined by
    the file service, not silently accepted.

An S3/object-cloud backend can be added later by implementing ``ObjectStorage``
without touching the project domain.
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings

_KEY_RE = re.compile(r"^[0-9a-f]{32}$")
_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_READ_CHUNK = 64 * 1024

# Formats that must never be served or executed without a real malware scanner.
_DANGEROUS_EXTENSIONS = frozenset({
    "exe", "dll", "so", "dylib", "bin", "com", "scr", "msi", "bat", "cmd",
    "sh", "bash", "zsh", "ps1", "psm1", "vbs", "vbe", "js", "mjs", "cjs",
    "jar", "app", "apk", "deb", "rpm", "pkg", "run", "elf", "o", "a",
    "py", "pyc", "rb", "pl", "php", "php5", "phtml", "cgi", "wasm",
})
_DANGEROUS_MEDIA_PREFIXES = ("application/x-executable", "application/x-sharedlib",
                             "application/x-mach-binary", "application/x-dosexec")
_DANGEROUS_MEDIA_EXACT = frozenset({
    "application/x-sh", "application/x-shellscript", "text/x-shellscript",
    "application/x-msdownload", "application/x-msdos-program", "application/vnd.microsoft.portable-executable",
})

_STORAGE_ERROR_TOO_LARGE = "UPLOAD_TOO_LARGE"


class UploadTooLarge(Exception):
    """Raised when a streamed upload exceeds the configured byte ceiling."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"Upload exceeds the {limit}-byte limit.")
        self.limit = limit
        self.code = _STORAGE_ERROR_TOO_LARGE


class StoredObjectMissing(Exception):
    """Raised when a persisted object key has no bytes on disk."""


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    checksum_sha256: str
    byte_size: int


def sanitize_filename(raw: str | None) -> str:
    """Reduce any client filename to a safe basename. Never used as a filesystem
    path — only for display and Content-Disposition."""
    candidate = os.path.basename((raw or "").strip().replace("\\", "/"))
    candidate = candidate.replace("\x00", "")
    candidate = _SAFE_CHARS.sub("_", candidate).strip("._-")
    if not candidate or set(candidate) <= {"_"}:
        return "upload"
    return candidate[:180]


def classify_upload(safe_filename: str, media_type: str | None) -> tuple[str, str | None]:
    """Return (storage_state, quarantine_reason).

    Dangerous formats are QUARANTINED with an honest reason; everything else is
    STORED. We never claim a clean malware scan — the scan state is tracked
    separately as SCAN_NOT_CONNECTED at the call site.
    """
    ext = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else ""
    media = (media_type or "").split(";", 1)[0].strip().lower()
    dangerous = (
        ext in _DANGEROUS_EXTENSIONS
        or media in _DANGEROUS_MEDIA_EXACT
        or any(media.startswith(prefix) for prefix in _DANGEROUS_MEDIA_PREFIXES)
    )
    if dangerous:
        return "QUARANTINED", f"Executable or script format '.{ext or media or 'unknown'}' is quarantined; no malware scanner is connected."
    return "STORED", None


class ObjectStorage(Protocol):
    async def put(self, chunks: AsyncIterator[bytes], *, max_bytes: int) -> StoredObject: ...
    def read_chunks(self, object_key: str) -> Iterator[bytes]: ...
    def verify(self, object_key: str, expected_sha256: str) -> bool: ...
    def delete(self, object_key: str) -> bool: ...
    def exists(self, object_key: str) -> bool: ...


class LocalObjectStorage:
    """Filesystem-backed object store rooted at a runtime data directory."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._root, 0o700)
        except PermissionError:  # pragma: no cover - best effort on shared hosts
            pass

    @property
    def root(self) -> Path:
        return self._root

    def _path_for(self, object_key: str, *, create_parents: bool = False) -> Path:
        if not _KEY_RE.match(object_key):
            raise ValueError("Malformed object key.")
        parent = self._root / object_key[:2] / object_key[2:4]
        if create_parents:
            parent.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(parent.parent, 0o700)
                os.chmod(parent, 0o700)
            except PermissionError:  # pragma: no cover
                pass
        # Defense in depth: the shard directory must resolve inside the root. The
        # leaf itself is NOT resolved here — a symlinked leaf is refused explicitly
        # by _resolved_regular_file's is_symlink() check before any read.
        if parent.exists() and not parent.resolve().is_relative_to(self._root):
            raise ValueError("Resolved object path escapes the storage root.")
        return parent / object_key

    async def put(self, chunks: AsyncIterator[bytes], *, max_bytes: int) -> StoredObject:
        object_key = uuid.uuid4().hex
        final_path = self._path_for(object_key, create_parents=True)
        tmp_path = final_path.with_name(f".{object_key}.tmp-{uuid.uuid4().hex}")
        digest = hashlib.sha256()
        size = 0
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as handle:
                async for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > max_bytes:
                        raise UploadTooLarge(max_bytes)
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, final_path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
        checksum = digest.hexdigest()
        # Re-verify from disk: the persisted bytes must match what we streamed.
        if not self.verify(object_key, checksum):  # pragma: no cover - integrity guard
            self.delete(object_key)
            raise OSError("Stored object failed post-write checksum verification.")
        return StoredObject(object_key=object_key, checksum_sha256=checksum, byte_size=size)

    def _resolved_regular_file(self, object_key: str) -> Path:
        path = self._path_for(object_key)
        # Refuse symlinks: only a real regular file inside the root may be read.
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise StoredObjectMissing(object_key)
        return path

    def read_chunks(self, object_key: str) -> Iterator[bytes]:
        path = self._resolved_regular_file(object_key)
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(_READ_CHUNK)
                if not chunk:
                    break
                yield chunk

    def read_bytes(self, object_key: str) -> bytes:
        path = self._resolved_regular_file(object_key)
        return path.read_bytes()

    def verify(self, object_key: str, expected_sha256: str) -> bool:
        try:
            path = self._resolved_regular_file(object_key)
        except StoredObjectMissing:
            return False
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(_READ_CHUNK), b""):
                digest.update(chunk)
        return digest.hexdigest() == expected_sha256

    def exists(self, object_key: str) -> bool:
        try:
            self._resolved_regular_file(object_key)
            return True
        except (StoredObjectMissing, ValueError):
            return False

    def iter_object_keys(self) -> Iterator[str]:
        """Yield every stored object key on disk, skipping in-flight temp files.

        Used by storage-hygiene reconciliation to find objects whose owning
        database record was lost. In-flight ``.{key}.tmp-*`` files are dot-
        prefixed and never match the key pattern, so they are ignored."""
        for path in self._root.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            if _KEY_RE.match(path.name):
                yield path.name

    def delete(self, object_key: str) -> bool:
        try:
            path = self._path_for(object_key)
        except ValueError:
            return False
        if path.is_symlink() or (path.exists() and not path.is_file()):
            return False
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False


_storage: LocalObjectStorage | None = None


def get_object_storage() -> LocalObjectStorage:
    """Process-wide local object store, rooted from settings."""
    global _storage
    settings = get_settings()
    if _storage is None or str(_storage.root) != str(Path(settings.project_object_root).resolve()):
        _storage = LocalObjectStorage(settings.project_object_root)
    return _storage


async def bytes_stream(data: bytes, chunk: int = _READ_CHUNK) -> AsyncIterator[bytes]:
    """Adapt an in-memory payload (e.g. a generated archive) to the put() interface."""
    for start in range(0, len(data), chunk):
        yield data[start:start + chunk]
