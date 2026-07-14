const STORE_KEY = "nur.encryptedTalkDraftQueue.v1";
const SESSION_KEY = "nur.sessionDraftKey.v1";

type QueuedDraft = { iv: string; ciphertext: string; created_at: string };

export async function queueEncryptedDraft(text: string): Promise<void> {
  if (!crypto.subtle || !text.trim()) return;
  const key = await draftKey();
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(text);
  const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, encoded);
  const rows = readQueue();
  rows.push({
    iv: b64(iv),
    ciphertext: b64(new Uint8Array(ciphertext)),
    created_at: new Date().toISOString(),
  });
  localStorage.setItem(STORE_KEY, JSON.stringify(rows.slice(-20)));
}

export async function readEncryptedDraftQueue(): Promise<string[]> {
  if (!crypto.subtle) return [];
  const key = await draftKey();
  const rows = readQueue();
  const out: string[] = [];
  for (const row of rows) {
    try {
      const iv = fromB64(row.iv);
      const ciphertext = fromB64(row.ciphertext);
      const plain = await crypto.subtle.decrypt(
        { name: "AES-GCM", iv: asBuffer(iv) },
        key,
        asBuffer(ciphertext),
      );
      out.push(new TextDecoder().decode(plain));
    } catch {
      // A previous browser session key cannot decrypt current drafts; keep fail-closed.
    }
  }
  return out;
}

export function clearEncryptedDraftQueue(): void {
  localStorage.removeItem(STORE_KEY);
}

function readQueue(): QueuedDraft[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORE_KEY) || "[]") as QueuedDraft[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function draftKey(): Promise<CryptoKey> {
  const existing = sessionStorage.getItem(SESSION_KEY);
  if (existing) {
    return crypto.subtle.importKey("raw", asBuffer(fromB64(existing)), "AES-GCM", false, ["encrypt", "decrypt"]);
  }
  const raw = crypto.getRandomValues(new Uint8Array(32));
  sessionStorage.setItem(SESSION_KEY, b64(raw));
  return crypto.subtle.importKey("raw", asBuffer(raw), "AES-GCM", false, ["encrypt", "decrypt"]);
}

function b64(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes));
}

function fromB64(value: string): Uint8Array {
  return Uint8Array.from(atob(value), c => c.charCodeAt(0));
}

function asBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}
