export const V197_ACCESSIBLE_VIEWPORT_MARKER = "nurAccessibleViewport";

/** Preserve responsive sizing while allowing browser and assistive zoom. */
export function ensureV197AccessibleViewport(document: Document): HTMLMetaElement | null {
  const viewport = document.querySelector<HTMLMetaElement>('meta[name="viewport"]');
  if (!viewport) return null;
  if (viewport.dataset[V197_ACCESSIBLE_VIEWPORT_MARKER] === "true") return viewport;

  const directives = viewport.content
    .split(",")
    .map(directive => directive.trim())
    .filter(Boolean)
    .filter(directive => !/^(maximum-scale|minimum-scale|user-scalable)\s*=/i.test(directive));
  const hasWidth = directives.some(directive => /^width\s*=/i.test(directive));
  const hasInitialScale = directives.some(directive => /^initial-scale\s*=/i.test(directive));
  if (!hasWidth) directives.unshift("width=device-width");
  if (!hasInitialScale) directives.push("initial-scale=1.0");

  viewport.content = directives.join(", ");
  viewport.dataset[V197_ACCESSIBLE_VIEWPORT_MARKER] = "true";
  return viewport;
}
