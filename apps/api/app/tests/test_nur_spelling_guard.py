"""The product name is NUR — never a phonetic variant.

This guard fails when a forbidden spelling of the product name appears as a
standalone word in first-party product material. Personal names that merely
contain the letters (for example "Mahnoor") never trip the word-boundary
match. Documentation explaining this law and explicit test fixtures are the
only sanctioned exceptions."""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]

FORBIDDEN = re.compile(r"\bnoor\b", re.IGNORECASE)

SCAN_ROOTS = (
    "apps/api/app",
    "apps/api/alembic",
    "apps/web/src",
    "apps/web/e2e",
    "apps/web/public",
    "apps/web/index.html",
    "apps/mobile",
    "docs",
    "infra",
    "scripts",
    "packages",
    "README.md",
    "RUNBOOK.md",
    "DEMO_SCRIPT.md",
    "QUICKSTART_BOOT.md",
    "SECURITY_NOTES.md",
    "RUN_NUR.sh",
    "RUN_NUR.command",
    "START_NUR.sh",
    "START_NUR.desktop",
    "Makefile",
)

SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".css", ".html", ".md",
    ".json", ".jsonl", ".sh", ".sql", ".yml", ".yaml", ".toml", ".desktop",
    ".command", ".txt",
}

SKIP_DIR_NAMES = {
    "node_modules", ".venv", "venv", "dist", "build", ".next", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "coverage",
    "playwright-report", "test-results", ".git", ".nur-runtime", "checkpoint",
    "proof",
}

# The only sanctioned in-repo exceptions: this guard itself and explicit
# forbidden-spelling fixtures.
ALLOWED_RELATIVE = {
    "apps/api/app/tests/test_nur_spelling_guard.py",
}


def _scan_targets():
    for root in SCAN_ROOTS:
        path = REPO_ROOT / root
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for candidate in path.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() not in SUFFIXES:
                continue
            if any(part in SKIP_DIR_NAMES for part in candidate.parts):
                continue
            yield candidate


def test_product_name_is_always_nur():
    violations: list[str] = []
    for path in _scan_targets():
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative in ALLOWED_RELATIVE:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if FORBIDDEN.search(line):
                violations.append(f"{relative}:{line_number}: {line.strip()[:120]}")
    assert not violations, (
        "The product name is NUR. Forbidden spellings found:\n" + "\n".join(violations[:40])
    )
