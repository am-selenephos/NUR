export const V197_LOCKUP_CLASS = "nur-v197-lockup";
export const V197_WORDMARK_CLASS = "nur-v197-wordmark";
export const V197_LOCKUP_SUBTITLE_CLASS = "nur-v197-lockup-subtitle";

const WORDMARK_CANDIDATES = [
  ".f4-brand-word",
  ".nur-holo-word",
  ".nur-v197-stable-wordmark",
  ".clean-audit-word",
  ".clean-brand-word",
  ".rebuilt-brand-word",
].join(",");

export function markV197HolographicWordmark(element: HTMLElement): void {
  if (element.textContent?.trim() !== "NUR") return;
  element.classList.add(V197_WORDMARK_CLASS);
  element.dataset.nurHolographicWordmark = "animated";
  element.dataset.nurWordmarkText = "NUR";
  if (element.closest(".universe-map-title")) {
    element.setAttribute("aria-label", "NUR");
  }
}

function lockPair(
  root: HTMLElement | null,
  wordSelector: string,
  subtitleSelector: string,
): boolean {
  if (!root) return false;
  const word = root.querySelector<HTMLElement>(wordSelector);
  const subtitle = root.querySelector<HTMLElement>(subtitleSelector);
  if (!word || !subtitle) return false;

  root.classList.add(V197_LOCKUP_CLASS);
  root.dataset.nurLockupAxis = "center";
  markV197HolographicWordmark(word);
  subtitle.classList.add(V197_LOCKUP_SUBTITLE_CLASS);
  return true;
}

export function lockV197BrandIdentity(document: Document): number {
  document.querySelectorAll<HTMLElement>(WORDMARK_CANDIDATES)
    .forEach(markV197HolographicWordmark);

  return [
    lockPair(
      document.querySelector<HTMLElement>(".f4-brand-copy"),
      ":scope > .f4-brand-word",
      ":scope > .f4-brand-sub",
    ),
    lockPair(
      document.querySelector<HTMLElement>(".universe-map-title"),
      ":scope > .nur-holo-word, :scope > .nur-v197-stable-wordmark",
      ":scope > .nur-master-subtitle, :scope > small",
    ),
  ].filter(Boolean).length;
}
