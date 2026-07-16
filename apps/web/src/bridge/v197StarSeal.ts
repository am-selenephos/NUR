const SVG_NS = "http://www.w3.org/2000/svg";

export const V197_STAR_SEAL_CLASS = "nur-star-seal";
export const V197_STAR_SEAL_SPRITE_ID = "nur-v197-star-seal-sprite";
export const V197_STAR_SEAL_SYMBOL_ID = "nur-v197-star-seal-symbol";
export const V197_CONTROL_STAR_SEAL_CLASS = "nur-star-seal--control";
export const V197_STATE_STAR_SEAL_CLASS = "nur-star-seal--state";

export type V197StarSealSize = 12 | 16 | 20 | 24 | 32;

const SIZES: readonly V197StarSealSize[] = [12, 16, 20, 24, 32];
const controlSealObservers = new WeakMap<Document, MutationObserver>();
const AUTHENTIC_HOST_ATTRIBUTE = "data-nur-authentic-star-host";

const PRIMARY_CONTROL_SELECTOR = [
  ".f4-primary",
  ".f4-submit",
  ".thought-send-button",
  ".universe-send",
].join(",");

const SELECTED_STATE_HOST_SELECTOR = [
  ".clean-nav-button.active > .clean-nav-glyph",
  ".scope-option[aria-selected='true']",
  ".scope-option[aria-checked='true']",
  ".audit-scope.selected",
  ".clean-scope.selected",
].join(",");

function svgElement<K extends keyof SVGElementTagNameMap>(
  document: Document,
  tag: K,
  attributes: Record<string, string> = {},
): SVGElementTagNameMap[K] {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
  return node;
}

function stop(document: Document, offset: string, color: string, opacity = "1"): SVGStopElement {
  return svgElement(document, "stop", {
    offset,
    "stop-color": color,
    "stop-opacity": opacity,
  });
}

function linearGradient(
  document: Document,
  id: string,
  stops: Array<[string, string, string?]>,
  attributes: Record<string, string> = {},
): SVGLinearGradientElement {
  const gradient = svgElement(document, "linearGradient", { id, ...attributes });
  stops.forEach(([offset, color, opacity]) => gradient.append(stop(document, offset, color, opacity)));
  return gradient;
}

function appendPaths(
  document: Document,
  host: SVGElement,
  paths: Array<{ d: string; fill: string; className?: string; opacity?: string }>,
): void {
  paths.forEach(path => {
    host.append(svgElement(document, "path", {
      d: path.d,
      fill: path.fill,
      class: path.className ?? "",
      ...(path.opacity ? { opacity: path.opacity } : {}),
    }));
  });
}

export function ensureV197StarSealSprite(document: Document): SVGSVGElement {
  const existing = document.getElementById(V197_STAR_SEAL_SPRITE_ID) as unknown as SVGSVGElement | null;
  if (existing) return existing;

  const sprite = svgElement(document, "svg", {
    id: V197_STAR_SEAL_SPRITE_ID,
    class: "nur-star-seal-sprite",
    width: "0",
    height: "0",
    "aria-hidden": "true",
    focusable: "false",
  });
  sprite.dataset.nurLayer = "v197-star-seal-sprite";

  const defs = svgElement(document, "defs");
  const halo = svgElement(document, "radialGradient", { id: "nur-star-seal-halo" });
  halo.append(
    stop(document, "0%", "#fff8df", ".42"),
    stop(document, "20%", "#ffd35a", ".22"),
    stop(document, "45%", "#ff3a9e", ".1"),
    stop(document, "68%", "#21e8ff", ".07"),
    stop(document, "100%", "#843dff", "0"),
  );
  const core = svgElement(document, "radialGradient", {
    id: "nur-star-seal-core",
    cx: "34%",
    cy: "28%",
    r: "76%",
  });
  core.append(
    stop(document, "0%", "#ffffff"),
    stop(document, "24%", "#fff8df"),
    stop(document, "52%", "#f8d98a"),
    stop(document, "76%", "#ffd35a"),
    stop(document, "100%", "#c9942f"),
  );
  defs.append(
    halo,
    core,
    linearGradient(document, "nur-star-seal-ray-gold", [
      ["0%", "#fff8df", "0"],
      ["62%", "#ffd35a", ".68"],
      ["100%", "#fff8df", "1"],
    ], { x1: "0", y1: "0", x2: "0", y2: "1" }),
    linearGradient(document, "nur-star-seal-ray-pink", [
      ["0%", "#ff79c8", "0"],
      ["62%", "#ff3a9e", ".66"],
      ["100%", "#fff8df", ".96"],
    ]),
    linearGradient(document, "nur-star-seal-ray-cyan", [
      ["0%", "#8af5ff", "0"],
      ["62%", "#21e8ff", ".64"],
      ["100%", "#fff8df", ".96"],
    ]),
    linearGradient(document, "nur-star-seal-shard", [
      ["0%", "#843dff", ".12"],
      ["38%", "#21e8ff", ".58"],
      ["70%", "#ff3a9e", ".66"],
      ["100%", "#ffd35a", ".9"],
    ]),
  );

  const symbol = svgElement(document, "symbol", {
    id: V197_STAR_SEAL_SYMBOL_ID,
    viewBox: "0 0 64 64",
  });
  symbol.append(
    svgElement(document, "circle", {
      class: "nur-star-seal__halo",
      cx: "32",
      cy: "32",
      r: "29",
      fill: "url(#nur-star-seal-halo)",
    }),
    svgElement(document, "circle", {
      class: "nur-star-seal__energy",
      cx: "32",
      cy: "32",
      r: "17.5",
      fill: "none",
      stroke: "#ffd35a",
      "stroke-opacity": ".34",
      "stroke-width": ".7",
      "stroke-dasharray": "17 8 4 12",
    }),
    svgElement(document, "circle", {
      class: "nur-star-seal__refraction",
      cx: "32",
      cy: "32",
      r: "21.5",
      fill: "none",
      stroke: "url(#nur-star-seal-shard)",
      "stroke-opacity": ".28",
      "stroke-width": ".55",
      "stroke-dasharray": "3 13 8 15",
    }),
  );

  const primary = svgElement(document, "g", { class: "nur-star-seal__primary" });
  appendPaths(document, primary, [
    { d: "M32 1.5 L35.1 27.8 L32 32 L28.9 27.8 Z", fill: "url(#nur-star-seal-ray-gold)" },
    { d: "M62.5 32 L36.2 35.1 L32 32 L36.2 28.9 Z", fill: "url(#nur-star-seal-ray-cyan)" },
    { d: "M32 62.5 L28.9 36.2 L32 32 L35.1 36.2 Z", fill: "url(#nur-star-seal-ray-gold)" },
    { d: "M1.5 32 L27.8 28.9 L32 32 L27.8 35.1 Z", fill: "url(#nur-star-seal-ray-pink)" },
  ]);

  const shards = svgElement(document, "g", { class: "nur-star-seal__shards" });
  appendPaths(document, shards, [
    { d: "M10.1 10.8 L28.1 28.9 L32 32 L27.1 30.8 Z", fill: "url(#nur-star-seal-shard)", opacity: ".78" },
    { d: "M53.8 10.3 L33.2 27.7 L32 32 L35.4 29.4 Z", fill: "url(#nur-star-seal-shard)", opacity: ".72" },
    { d: "M53.6 53.9 L35.1 34.8 L32 32 L33.4 36.6 Z", fill: "url(#nur-star-seal-shard)", opacity: ".76" },
    { d: "M10.4 53.5 L28.8 35.1 L32 32 L30.5 36.4 Z", fill: "url(#nur-star-seal-shard)", opacity: ".7" },
    { d: "M21.5 3.8 L30.1 27.9 L32 32 L28.2 29.7 Z", fill: "#ff79c8", opacity: ".4" },
    { d: "M60.2 21.6 L36 30.2 L32 32 L34.4 28.3 Z", fill: "#8af5ff", opacity: ".4" },
    { d: "M42.5 60.2 L33.9 36.1 L32 32 L35.8 34.2 Z", fill: "#c16bff", opacity: ".38" },
    { d: "M3.9 42.3 L28 33.8 L32 32 L29.7 35.7 Z", fill: "#ffd35a", opacity: ".44" },
  ]);

  const coreGroup = svgElement(document, "g", { class: "nur-star-seal__core" });
  coreGroup.append(
    svgElement(document, "path", {
      d: "M32 26.4 L37.6 32 L32 37.6 L26.4 32 Z",
      fill: "url(#nur-star-seal-core)",
      stroke: "#fff8df",
      "stroke-opacity": ".74",
      "stroke-width": ".7",
    }),
    svgElement(document, "path", { d: "M32 26.4 L32 32 L26.4 32 Z", fill: "#ffffff", opacity: ".74" }),
    svgElement(document, "path", { d: "M32 26.4 L37.6 32 L32 32 Z", fill: "#8af5ff", opacity: ".38" }),
    svgElement(document, "path", { d: "M37.6 32 L32 37.6 L32 32 Z", fill: "#c16bff", opacity: ".34" }),
    svgElement(document, "path", { d: "M32 37.6 L26.4 32 L32 32 Z", fill: "#ff79c8", opacity: ".32" }),
    svgElement(document, "circle", { cx: "30.2", cy: "29.8", r: ".8", fill: "#ffffff", opacity: ".98" }),
  );

  symbol.append(primary, shards, coreGroup);
  sprite.append(defs, symbol);
  (document.body ?? document.documentElement).prepend(sprite);
  return sprite;
}

function nearestSize(value: number): V197StarSealSize {
  return SIZES.reduce((nearest, size) => (
    Math.abs(size - value) < Math.abs(nearest - value) ? size : nearest
  ), 20);
}

function renderedHostSize(host: HTMLElement): V197StarSealSize {
  if (host.closest(".universe-system-node")) return 24;
  if (host.closest(".clean-system-row")) return 16;
  const rect = host.getBoundingClientRect();
  const measured = Math.max(rect.width, rect.height);
  if (measured > 0) return nearestSize(measured);
  const declared = Number(host.dataset.nurStarSize ?? 20);
  return nearestSize(Number.isFinite(declared) ? declared : 20);
}

export function createV197StarSeal(
  document: Document,
  size: V197StarSealSize = 20,
  twinkle = false,
): SVGSVGElement {
  ensureV197StarSealSprite(document);
  const seal = svgElement(document, "svg", {
    class: `${V197_STAR_SEAL_CLASS} ${V197_STAR_SEAL_CLASS}--${size}`,
    viewBox: "0 0 64 64",
    width: String(size),
    height: String(size),
    "aria-hidden": "true",
    focusable: "false",
  });
  seal.dataset.nurStarSize = String(size);
  seal.dataset.nurStarTwinkle = String(twinkle);
  seal.append(svgElement(document, "use", { href: `#${V197_STAR_SEAL_SYMBOL_ID}` }));
  return seal;
}

function ensureControlSeal(
  document: Document,
  host: HTMLElement,
  size: V197StarSealSize,
  stateSeal: boolean,
): number {
  const kind = stateSeal ? V197_STATE_STAR_SEAL_CLASS : V197_CONTROL_STAR_SEAL_CLASS;
  const existing = host.querySelector<SVGSVGElement>(`:scope > .${kind}`);
  if (existing) return 0;

  const seal = createV197StarSeal(document, size, stateSeal);
  seal.classList.add(kind);
  host.prepend(seal);
  host.classList.add(stateSeal ? "nur-has-state-star-seal" : "nur-has-control-star-seal");
  host.dataset.nurStarSeal = stateSeal ? "selected-control" : "primary-control";
  return 1;
}

function syncV197ControlSeals(document: Document): number {
  let installed = 0;

  document.querySelectorAll<HTMLElement>(PRIMARY_CONTROL_SELECTOR).forEach(control => {
    installed += ensureControlSeal(document, control, control.matches(".compact") ? 16 : 20, false);
  });

  const selectedHosts = new Set(document.querySelectorAll<HTMLElement>(SELECTED_STATE_HOST_SELECTOR));
  document.querySelectorAll<SVGSVGElement>(`.${V197_STATE_STAR_SEAL_CLASS}`).forEach(seal => {
    const host = seal.parentElement;
    if (host && selectedHosts.has(host)) return;
    seal.remove();
    host?.classList.remove("nur-has-state-star-seal");
    if (host?.dataset.nurStarSeal === "selected-control") delete host.dataset.nurStarSeal;
  });
  selectedHosts.forEach(host => {
    installed += ensureControlSeal(document, host, 20, true);
  });
  return installed;
}

function observeV197ControlSeals(document: Document): void {
  if (controlSealObservers.has(document)) return;
  const frameWindow = document.defaultView;
  const root = document.getElementById("nur-front-v61") ?? document.body;
  if (!frameWindow || !root) return;

  let frame: number | null = null;
  const observer = new frameWindow.MutationObserver(() => {
    if (frame !== null) return;
    frame = frameWindow.requestAnimationFrame(() => {
      frame = null;
      syncV197ControlSeals(document);
    });
  });
  observer.observe(root, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["class", "aria-selected", "aria-checked"],
  });
  controlSealObservers.set(document, observer);
}

export function installV197StarSeals(document: Document): number {
  let installed = 0;
  document.querySelectorAll<HTMLElement>(".nur-exact-mini-host").forEach(host => {
    if (host.querySelector(`:scope > .${V197_STAR_SEAL_CLASS}`)) return;
    const sourceModule = host.querySelector<HTMLElement>(":scope > .nur-star-module");
    if (!sourceModule) return;

    const control = host.closest("button, a");
    const active = Boolean(control?.matches(".active, [aria-current='page'], [aria-selected='true']"));
    host.replaceChildren(createV197StarSeal(document, renderedHostSize(host), active));
    host.dataset.nurMiniCompacted = "true";
    host.dataset.nurStarSeal = "authentic";
    const visualHost = host.matches(".nur-exact-icon-shell")
      ? host
      : host.closest<HTMLElement>(".nur-exact-icon-shell");
    visualHost?.setAttribute(AUTHENTIC_HOST_ATTRIBUTE, "true");
    installed += 1;
  });
  installed += syncV197ControlSeals(document);
  observeV197ControlSeals(document);
  return installed;
}
