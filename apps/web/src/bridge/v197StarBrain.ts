import V43_STAR_BRAIN_RUNTIME from "./v43StarBrainRuntime.js?raw";
import { ensureV197AccessibleViewport } from "./v197Accessibility";

export const V197_STAR_BRAIN_CANVAS_ID = "nur-brain-canvas";
export const V197_STAR_BRAIN_HOST_ID = "front-nur-star";
const V197_STAR_BRAIN_SCRIPT_ID = "nur-v43-exact-star-brain-runtime";
const V43_STAR_BRAIN_RUNTIME_HASH = "ee34405b119b8f2d7b6a5b4b7fdedff2e6875f9bd7d472aff6ab5b8473b8d347";

type V197StarBrainSurface = "entry" | "today" | "universe" | "map";

type ExactBrainWindow = Window & {
  nurStarBrain?: {
    storm: (power?: number) => void;
    absorb: () => void;
    shatter: () => void;
    firePulse: (from?: number) => void;
  };
};

type VeiledContext = CanvasRenderingContext2D & { __v197Veil?: boolean };

type V197StarBrainController = {
  observer: MutationObserver;
  frame: number | null;
};

const starBrainControllers = new WeakMap<Document, V197StarBrainController>();
const starBrainHosts = new WeakMap<Document, HTMLElement>();

function resolveV197StarBrainHost(document: Document): {
  host: HTMLElement;
  surface: V197StarBrainSurface;
} | null {
  const todayPage = document.querySelector<HTMLElement>("#page-today.active");
  const todayHost = todayPage?.querySelector<HTMLElement>(".orbit-star-zone > .f4-core");
  if (todayHost) return { host: todayHost, surface: "today" };

  const universeHost = document.querySelector<HTMLElement>(
    "body.universe-edition #page-systems.active .universe-map-panel > .universe-master-star",
  );
  if (universeHost) return { host: universeHost, surface: "universe" };

  const mapHost = document.querySelector<HTMLElement>(
    "body.universe-edition #page-universe-map.active .lens-map-master",
  );
  if (mapHost) return { host: mapHost, surface: "map" };

  const entryHost = document.querySelector<HTMLElement>("#nur-front-v61 #f4-core");
  return entryHost ? { host: entryHost, surface: "entry" } : null;
}

function removeLegacyMasterStar(host: HTMLElement, surface: V197StarBrainSurface): void {
  const selector = surface === "universe" || surface === "map"
    ? ":scope > .f4-core, :scope > .spark, :scope > .f4-master-star"
    : ":scope > .spark, :scope > .f4-master-star";

  host.querySelectorAll<HTMLElement>(selector).forEach(element => element.remove());
  host.dataset.nurLegacyMasterStar = "removed";
}

export function placeV197StarBrainHost(document: Document): HTMLElement | null {
  document.body?.classList.toggle(
    "nur-v197-systems-active",
    Boolean(document.querySelector("#page-systems.active")),
  );
  const resolved = resolveV197StarBrainHost(document);
  if (!resolved) return null;
  const { host: canonicalHost, surface } = resolved;
  canonicalHost.dataset.nurStarBrainSurface = surface;
  removeLegacyMasterStar(canonicalHost, surface);

  let brainHost = (document.getElementById(V197_STAR_BRAIN_HOST_ID) as HTMLElement | null)
    ?? starBrainHosts.get(document)
    ?? null;
  if (!brainHost) {
    brainHost = document.createElement("div");
    brainHost.id = V197_STAR_BRAIN_HOST_ID;
    brainHost.dataset.nurSource = "exact-v43-front-page-signup-v7-star-brain";
    starBrainHosts.set(document, brainHost);
  }
  if (brainHost.parentElement !== canonicalHost) canonicalHost.append(brainHost);
  brainHost.dataset.nurSurface = surface;
  brainHost.dataset.nurDispersal = "radial-circle";
  brainHost.dataset.nurGalaxyPaint = "v197-simple-galaxy-particle-v1";
  brainHost.setAttribute("aria-label", surface === "today" ? "Wake the NUR mind" : "Wake the NUR star brain");
  brainHost.setAttribute("role", "button");
  brainHost.tabIndex = 0;
  return brainHost;
}

function observeV197StarBrainPlacement(document: Document, frameWindow: Window): void {
  if (starBrainControllers.has(document)) return;
  const root = document.getElementById("nur-front-v61") ?? document.body;
  if (!root) return;

  const constructors = frameWindow as unknown as {
    MutationObserver: typeof MutationObserver;
    HTMLElement: typeof HTMLElement;
  };
  const controller: V197StarBrainController = { observer: null as unknown as MutationObserver, frame: null };
  const observer = new constructors.MutationObserver((records: MutationRecord[]) => {
    const routeChanged = records.some(record => (
      record.type === "attributes"
      || Array.from(record.addedNodes).some(node => node instanceof constructors.HTMLElement)
      || Array.from(record.removedNodes).some(node => node instanceof constructors.HTMLElement)
    ));
    if (!routeChanged || controller.frame !== null) return;
    controller.frame = frameWindow.requestAnimationFrame(() => {
      controller.frame = null;
      placeV197StarBrainHost(document);
    });
  });
  controller.observer = observer;
  observer.observe(root, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["class"],
  });
  starBrainControllers.set(document, controller);
}

/** Match the reference V197 full-sky wash attenuation without touching stars. */
export function ensureV197BlackGalaxy(document: Document): void {
  const canvas = document.querySelector<HTMLCanvasElement>("#space3d");
  const frameWindow = document.defaultView;
  if (!canvas || !frameWindow) return;
  const context = canvas.getContext("2d") as VeiledContext | null;
  if (!context || context.__v197Veil) return;

  context.__v197Veil = true;
  const originalFillRect = context.fillRect.bind(context);
  context.fillRect = (x: number, y: number, width: number, height: number) => {
    if (x === 0 && y === 0 && width > frameWindow.innerWidth * .92 && height > frameWindow.innerHeight * .92) {
      const alpha = context.globalAlpha;
      context.globalAlpha = alpha * .5;
      originalFillRect(x, y, width, height);
      context.globalAlpha = alpha;
      return;
    }
    originalFillRect(x, y, width, height);
  };
}

/**
 * Mount the founder-approved V43 V7 anatomy with the NUR sparkle-and-stem
 * extension. The bridge only provides the canonical host, removes any already
 * mounted legacy canvas, and supplies the circular CSS dispersal boundary.
 */
export function ensureV197StarBrain(document: Document): HTMLCanvasElement | null {
  ensureV197AccessibleViewport(document);
  const frameWindow = document.defaultView as ExactBrainWindow | null;
  if (!frameWindow) return null;
  const brainHost = placeV197StarBrainHost(document);
  if (!brainHost) return null;
  brainHost.dataset.nurModel = "v43-v7-spark-stem";
  brainHost.dataset.nurVariant = "galaxy-rig-brainstem-v2";
  observeV197StarBrainPlacement(document, frameWindow);

  if (!document.getElementById(V197_STAR_BRAIN_SCRIPT_ID)) {
    for (const canvasId of [V197_STAR_BRAIN_CANVAS_ID, "nur-brain-canvas-v197"]) {
      const existingCanvas = document.getElementById(canvasId) as HTMLCanvasElement | null;
      if (!existingCanvas) continue;
      try {
        existingCanvas.width = 0;
        existingCanvas.height = 0;
      } catch {
        // A canvas may have been mounted by an older source before the bridge.
      }
      existingCanvas.remove();
    }
    const script = document.createElement("script");
    script.id = V197_STAR_BRAIN_SCRIPT_ID;
    script.dataset.nurSource = "exact-v43-front-page-signup-v7-star-brain";
    script.dataset.nurVariant = "galaxy-rig-brainstem-v2";
    script.dataset.nurRuntimeHash = V43_STAR_BRAIN_RUNTIME_HASH;
    script.textContent = V43_STAR_BRAIN_RUNTIME;
    (document.body ?? document.head).append(script);
  }

  if (brainHost.dataset.nurExactBridgeBound !== "true") {
    brainHost.dataset.nurExactBridgeBound = "true";
    /* The reference page's existing V4 host listener supplies this class.
     * Canonical V197 has different hosts, so bridge only that event signal. */
    brainHost.addEventListener("click", () => {
      brainHost.dataset.nurLastInteraction = "shatter";
      brainHost?.classList.remove("is-bursting");
      void brainHost?.offsetWidth;
      brainHost?.classList.add("is-bursting");
      frameWindow.setTimeout(() => brainHost?.classList.remove("is-bursting"), 90);
    });
    brainHost.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      brainHost?.click();
    });
  }

  return document.getElementById(V197_STAR_BRAIN_CANVAS_ID) as HTMLCanvasElement | null;
}
