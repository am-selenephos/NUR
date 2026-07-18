import V197_FUNCTIONAL_CSS from "../styles/v197-functional.css?raw";
import V197_COSMIC_SKIN_CSS from "../styles/v197-cosmic-skin.css?raw";
import V197_STAR_SEAL_CSS from "../styles/v197-star-seal.css?raw";
import { lockV197BrandIdentity } from "./v197Brand";
import { V197_FONT_FACE_CSS } from "./v197Fonts";
import { ensureV197BlackGalaxy, ensureV197StarBrain } from "./v197StarBrain";
import { installV197StarSeals, V197_STAR_SEAL_CLASS } from "./v197StarSeal";

export const V197_PREMIUM_POLISH_STYLE_ID = "nur-v197-track-a-premium-polish";
export const V197_STABLE_WORDMARK_CLASS = "nur-v197-stable-wordmark";
export const V197_COMPACT_MINI_STAR_CLASS = V197_STAR_SEAL_CLASS;
export const V197_ENTRY_POLISH_STYLE_ID = "nur-v197-entry-premium-polish";
export {
  V197_LOCKUP_CLASS,
  V197_LOCKUP_SUBTITLE_CLASS,
  V197_WORDMARK_CLASS,
} from "./v197Brand";

const V197_PRESENTATION_CSS = [
  V197_FONT_FACE_CSS,
  V197_FUNCTIONAL_CSS,
  V197_STAR_SEAL_CSS,
  V197_COSMIC_SKIN_CSS,
].join("\n");

function ensureStableMapWordmark(document: Document): HTMLElement | null {
  const title = document.querySelector<HTMLElement>(".universe-map-title");
  const source = title?.querySelector<HTMLElement>(":scope > .nur-holo-word");
  if (!title || !source) return null;

  title.querySelectorAll<HTMLElement>(`:scope > .${V197_STABLE_WORDMARK_CLASS}`)
    .forEach(element => {
      if (element !== source) element.remove();
    });
  source.dataset.nurStableSource = "true";
  source.classList.add(V197_STABLE_WORDMARK_CLASS);
  source.textContent = "NUR";
  return source;
}

function relocateSystemsMantra(document: Document): HTMLElement | null {
  const mantra = document.querySelector<HTMLElement>(".universe-map-mantra");
  const heroCopy = document.querySelector<HTMLElement>("#page-systems .universe-hero-copy > div");
  if (!mantra || !heroCopy) return null;

  mantra.classList.add("nur-systems-epigraph");
  mantra.dataset.nurRelocated = "systems-hero";
  if (mantra.parentElement !== heroCopy) heroCopy.append(mantra);
  return mantra;
}

function labelCompactTopbarControls(document: Document): void {
  document.querySelectorAll<HTMLButtonElement>(".universe-nav-tabs button").forEach(button => {
    const label = button.querySelector("span")?.textContent?.trim();
    if (!label) return;
    button.setAttribute("aria-label", label);
    button.title = label;
  });

  const scope = document.querySelector<HTMLButtonElement>("#scope-open");
  if (scope) {
    scope.setAttribute("aria-label", "Privacy boundary");
    scope.title = "Privacy boundary";
  }
}

export function compactV197MiniStars(document: Document): number {
  return installV197StarSeals(document);
}

function installPresentationStyle(
  document: Document,
  styleId: string,
  layer: string,
): HTMLStyleElement {
  const existing = document.getElementById(styleId) as HTMLStyleElement | null;
  if (existing) return existing;

  const style = document.createElement("style");
  style.id = styleId;
  style.dataset.nurLayer = layer;
  style.textContent = V197_PRESENTATION_CSS;
  (document.body ?? document.head).append(style);
  return style;
}

function installEntrySheetState(document: Document): void {
  const root = document.documentElement;
  if (root.dataset.nurEntrySheetState === "bound") return;
  root.dataset.nurEntrySheetState = "bound";

  const sheet = document.querySelector<HTMLElement>("#f4-sheet");
  const sync = () => document.body?.classList.toggle(
    "nur-v197-auth-open",
    Boolean(sheet?.classList.contains("open")),
  );
  const openBeforeCanonicalHandler = (event: Event) => {
    const target = event.target as Element | null;
    if (!target?.closest("#f4-begin, #f4-signin, #f4-what, #f4-about-begin, [data-switch]")) return;
    document.body?.classList.add("nur-v197-auth-open");
  };

  document.addEventListener("click", openBeforeCanonicalHandler, true);
  sync();
  if (sheet && document.defaultView) {
    const observer = new document.defaultView.MutationObserver(sync);
    observer.observe(sheet, { attributes: true, attributeFilter: ["class"] });
  }
}

export function ensureV197EntryPolish(document: Document): HTMLStyleElement {
  const style = installPresentationStyle(
    document,
    V197_ENTRY_POLISH_STYLE_ID,
    "v197-native-entry-presentation",
  );
  installEntrySheetState(document);
  lockV197BrandIdentity(document);
  installV197StarSeals(document);
  ensureV197BlackGalaxy(document);
  ensureV197StarBrain(document);
  return style;
}

export function ensureV197PremiumPolish(document: Document): HTMLStyleElement {
  const style = installPresentationStyle(
    document,
    V197_PREMIUM_POLISH_STYLE_ID,
    "v197-native-universe-presentation",
  );
  compactV197MiniStars(document);
  ensureStableMapWordmark(document);
  lockV197BrandIdentity(document);
  relocateSystemsMantra(document);
  labelCompactTopbarControls(document);
  ensureV197BlackGalaxy(document);
  ensureV197StarBrain(document);
  return style;
}
