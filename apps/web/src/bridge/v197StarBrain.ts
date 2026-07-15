import V197_STAR_BRAIN_RUNTIME from "./v197StarBrainRuntime.js?raw";

export const V197_STAR_BRAIN_CANVAS_ID = "nur-brain-canvas-v197";
export const V197_STAR_BRAIN_HOST_ID = "front-nur-star";
const V197_STAR_BRAIN_SCRIPT_ID = "nur-v197-exact-star-brain-runtime";

type V197StarBrainSurface = "entry" | "universe";

type ExactBrainWindow = Window & {
  nurStarBrain?: {
    storm: (power?: number) => void;
    absorb: () => void;
    shatter: () => void;
    firePulse: (from?: number) => void;
  };
};

type VeiledContext = CanvasRenderingContext2D & { __v197Veil?: boolean };

function resolveV197StarBrainHost(document: Document): {
  host: HTMLElement;
  surface: V197StarBrainSurface;
} | null {
  const universeHost = document.querySelector<HTMLElement>(
    "body.universe-edition .universe-map-panel > .universe-master-star",
  );
  if (universeHost) return { host: universeHost, surface: "universe" };

  const entryHost = document.querySelector<HTMLElement>("#nur-front-v61 #f4-core");
  return entryHost ? { host: entryHost, surface: "entry" } : null;
}

function removeLegacyMasterStar(host: HTMLElement, surface: V197StarBrainSurface): void {
  const selector = surface === "universe"
    ? ":scope > .f4-core"
    : ":scope > .spark, :scope > .f4-master-star";

  host.querySelectorAll<HTMLElement>(selector).forEach(element => element.remove());
  host.dataset.nurLegacyMasterStar = "removed";
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
 * Mount the exact final `nur-v197-star-brain-galaxy-port` script extracted
 * byte-for-byte from the approved reference HTML. Only its expected host is
 * adapted to canonical V197; anatomy and stellar rendering remain untouched.
 */
export function ensureV197StarBrain(document: Document): HTMLCanvasElement | null {
  const resolved = resolveV197StarBrainHost(document);
  const frameWindow = document.defaultView as ExactBrainWindow | null;
  if (!resolved || !frameWindow) return null;
  const { host: canonicalHost, surface } = resolved;
  canonicalHost.dataset.nurStarBrainSurface = surface;
  removeLegacyMasterStar(canonicalHost, surface);

  let brainHost = document.getElementById(V197_STAR_BRAIN_HOST_ID) as HTMLElement | null;
  if (!brainHost) {
    brainHost = document.createElement("div");
    brainHost.id = V197_STAR_BRAIN_HOST_ID;
    brainHost.dataset.nurSource = "exact-v197-star-brain-galaxy-port";
    canonicalHost.append(brainHost);
  } else if (brainHost.parentElement !== canonicalHost) {
    canonicalHost.append(brainHost);
  }
  brainHost.dataset.nurSurface = surface;
  brainHost.setAttribute("role", "button");
  brainHost.tabIndex = 0;

  if (canonicalHost.dataset.nurStarBrainObserved !== "true") {
    canonicalHost.dataset.nurStarBrainObserved = "true";
    const FrameMutationObserver = (
      frameWindow as unknown as { MutationObserver: typeof MutationObserver }
    ).MutationObserver;
    const reconnect = new FrameMutationObserver(() => {
      removeLegacyMasterStar(canonicalHost, surface);
      if (!brainHost?.isConnected && canonicalHost.isConnected) canonicalHost.append(brainHost);
    });
    reconnect.observe(canonicalHost, { childList: true });
  }

  if (!document.getElementById(V197_STAR_BRAIN_SCRIPT_ID)) {
    const script = document.createElement("script");
    script.id = V197_STAR_BRAIN_SCRIPT_ID;
    script.dataset.nurSource = "exact-v197-star-brain-galaxy-port";
    script.textContent = V197_STAR_BRAIN_RUNTIME;
    (document.body ?? document.head).append(script);

  }

  if (brainHost.dataset.nurExactBridgeBound !== "true") {
    brainHost.dataset.nurExactBridgeBound = "true";
    /* The reference page's existing V4 host listener supplies this class.
     * Canonical V197 has different hosts, so bridge only that event signal. */
    brainHost.addEventListener("click", () => {
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
