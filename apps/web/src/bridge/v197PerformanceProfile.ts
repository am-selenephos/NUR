export const V197_RUNTIME_PROFILE_SCRIPT_ID = "nur-v197-runtime-performance-profile";

type Replacement = readonly [from: string, to: string];

const ENTRY_REPLACEMENTS: readonly Replacement[] = [
  ["DPR=Math.min(devicePixelRatio||1,1.65)", "DPR=Math.min(devicePixelRatio||1,1.2)"],
  ["(mobile?680:1140)", "(mobile?120:150)"],
  ["(mobile?460:720)", "(mobile?70:85)"],
  ["(mobile?192:320)", "(mobile?22:26)"],
  ["(mobile?44:76)", "(mobile?8:10)"],
  [".slice(0,130)", ".slice(0,18)"],
] as const;

const UNIVERSE_REPLACEMENTS: readonly Replacement[] = [
  ["DPR=Math.min(devicePixelRatio||1,1.5)", "DPR=Math.min(devicePixelRatio||1,.82)"],
  ["const PARTICLE_CAP=1880", "const PARTICLE_CAP=240"],
  [
    "const density=mobile?{galaxy:620,far:430,dust:118,super:32}:{galaxy:900,far:585,dust:165,super:48}",
    "const density=mobile?{galaxy:50,far:24,dust:8,super:4}:{galaxy:90,far:45,dust:12,super:6}",
  ],
  ["const nodeBudget=innerWidth<700?54:82", "const nodeBudget=innerWidth<700?12:18"],
  [
    "if(farAlpha>.095&&farR>.7)spike(q.x,q.y,farR*2.4,farCol,Math.min(.12,farAlpha*.24),phase);continue",
    "continue",
  ],
  [
    'if(p.kind==="dust"){const dr=',
    'if(!isS&&p.kind==="galaxy"){const simpleCol=p.prism?prismShift(p.col,p.prismPhase+t*p.prismSpeed+phase*.18,twinkle,false):p.col;const simpleR=Math.max(.52,rad*.82);c.fillStyle=`rgba(${simpleCol[0]},${simpleCol[1]},${simpleCol[2]},${Math.min(.92,alpha*2.35)})`;c.fillRect(q.x-simpleR*.5,q.y-simpleR*.5,simpleR,simpleR);if(alpha>.24&&rad>.82){c.strokeStyle=`rgba(${simpleCol[0]},${simpleCol[1]},${simpleCol[2]},${Math.min(.2,alpha*.42)})`;c.lineWidth=.42;c.beginPath();c.moveTo(q.x-simpleR*2.2,q.y);c.lineTo(q.x+simpleR*2.2,q.y);c.moveTo(q.x,q.y-simpleR*1.5);c.lineTo(q.x,q.y+simpleR*1.5);c.stroke()}continue}if(p.kind==="dust"){const dustR=Math.max(.5,rad*.9);c.fillStyle=`rgba(${p.col[0]},${p.col[1]},${p.col[2]},${Math.min(.36,alpha*1.7)})`;c.fillRect(q.x-dustR*.5,q.y-dustR*.5,dustR,dustR);continue}if(false&&p.kind==="dust"){const dr=',
  ],
  [
    "function scheduleFrame(){if(reduced||frameRAF)return;frameRAF=requestAnimationFrame(frame)}",
    'function scheduleFrame(){if(reduced||frameRAF)return;frameRAF=requestAnimationFrame(now=>{frameRAF=0;const active=document.documentElement.dataset.nurInteractionActive==="true",budget=active?16.7:__q<.45?33.3:__q<.7?25:20;if(now-last+1<budget){scheduleFrame();return}frame(now)})}',
  ],
] as const;

export type V197ProfileResult = {
  source: string;
  applied: boolean;
  replacementCount: number;
  failure?: string;
};

function replaceExactlyOnce(source: string, [from, to]: Replacement): V197ProfileResult {
  const first = source.indexOf(from);
  if (first < 0) {
    return { source, applied: false, replacementCount: 0, failure: `missing:${from.slice(0, 72)}` };
  }
  if (source.indexOf(from, first + from.length) >= 0) {
    return { source, applied: false, replacementCount: 0, failure: `duplicate:${from.slice(0, 72)}` };
  }
  return {
    source: `${source.slice(0, first)}${to}${source.slice(first + from.length)}`,
    applied: true,
    replacementCount: 1,
  };
}

export function applyV197PerformanceProfile(
  source: string,
  kind: "entry" | "universe",
): V197ProfileResult {
  const replacements = kind === "entry" ? ENTRY_REPLACEMENTS : UNIVERSE_REPLACEMENTS;
  let profiled = source;
  let replacementCount = 0;

  for (const replacement of replacements) {
    const result = replaceExactlyOnce(profiled, replacement);
    if (!result.applied) {
      return {
        source,
        applied: false,
        replacementCount: 0,
        failure: result.failure,
      };
    }
    profiled = result.source;
    replacementCount += result.replacementCount;
  }

  return { source: profiled, applied: true, replacementCount };
}

/*
 * The canonical host computes integrity against its untouched embedded bytes.
 * This bootstrap intercepts only the browser's srcdoc assignment and applies a
 * deterministic runtime quality profile. If any known signature drifts, the
 * original source is used and the host records a visible-to-tests fallback.
 */
export function buildV197PerformanceBootstrap(): string {
  const entry = JSON.stringify(ENTRY_REPLACEMENTS);
  const universe = JSON.stringify(UNIVERSE_REPLACEMENTS);
  return `<script id="${V197_RUNTIME_PROFILE_SCRIPT_ID}">
(() => {
  "use strict";
  const requested = new URLSearchParams(location.search).get("nur-quality");
  if (requested === "canonical") {
    document.documentElement.dataset.nurRuntimeProfile = "canonical";
    return;
  }
  const profiles = { entry: ${entry}, universe: ${universe} };
  const descriptor = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, "srcdoc");
  if (!descriptor || typeof descriptor.set !== "function" || typeof descriptor.get !== "function") {
    document.documentElement.dataset.nurRuntimeProfile = "canonical-fallback";
    document.documentElement.dataset.nurRuntimeProfileError = "srcdoc-descriptor";
    return;
  }
  const replaceOnce = (source, pair) => {
    const [from, to] = pair;
    const first = source.indexOf(from);
    if (first < 0 || source.indexOf(from, first + from.length) >= 0) return null;
    return source.slice(0, first) + to + source.slice(first + from.length);
  };
  Object.defineProperty(HTMLIFrameElement.prototype, "srcdoc", {
    configurable: descriptor.configurable,
    enumerable: descriptor.enumerable,
    get: descriptor.get,
    set(value) {
      let next = value;
      if (typeof value === "string") {
        const kind = value.includes("const PARTICLE_CAP=1880")
          ? "universe"
          : value.includes("V106: 100% denser actual galaxy seed")
            ? "entry"
            : null;
        if (kind) {
          for (const pair of profiles[kind]) {
            const replaced = replaceOnce(next, pair);
            if (replaced === null) {
              document.documentElement.dataset.nurRuntimeProfile = "canonical-fallback";
              document.documentElement.dataset.nurRuntimeProfileError = kind + "-signature";
              next = value;
              break;
            }
            next = replaced;
          }
          if (next !== value) {
            document.documentElement.dataset.nurRuntimeProfile = "balanced";
            document.documentElement.dataset["nur" + kind[0].toUpperCase() + kind.slice(1) + "Profile"] = "applied";
          }
        }
      }
      descriptor.set.call(this, next);
    },
  });
})();
</script>`;
}
