export const V197_SELECTORS = {
  entryStage: "#nur-entry-stage",
  universeStage: "#nur-universe-stage",
  page: (page: string) => `#page-${page}`,
  pageNav: (page: string) => `[data-page="${CSS.escape(page)}"]`,
  worldFocus: (focus: string) => `[data-world-focus="${CSS.escape(focus)}"], [data-world-tab="${CSS.escape(focus)}"]`,
  heroStats: ".universe-hero-stats > span",
  fieldReadout: ".universe-field-readout > span",
  contextTitle: "[data-context-title]",
  boundaryName: ".v172-boundary-current b",
  liveFeed: ".page-kicker",
  ownerStar: ".universe-top-tools > .nur-user",
  mapNodes: ".universe-system-node",
} as const;

export function selectRequired<T extends Element>(document: Document, selector: string): T {
  const node = document.querySelector<T>(selector);
  if (!node) throw new Error(`Canonical V197 selector is missing: ${selector}`);
  return node;
}
