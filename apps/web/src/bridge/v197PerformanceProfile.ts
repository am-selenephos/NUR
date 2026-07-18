export const V197_RUNTIME_PROFILE_SCRIPT_ID = "nur-v197-runtime-performance-profile";

type Replacement = readonly [from: string, to: string];

export const V197_GALAXY_STAR_PAINT = Object.freeze({
  minimumRadius: .52,
  radiusScale: .82,
  maximumBodyAlpha: .92,
  bodyAlphaScale: 2.35,
  flareAlphaThreshold: .24,
  flareRadiusThreshold: .82,
  maximumFlareAlpha: .2,
  flareAlphaScale: .42,
  horizontalFlareScale: 2.2,
  verticalFlareScale: 1.5,
  flareThickness: .42,
});

const GALAXY_STAR_PAINT_REPLACEMENT: Replacement = [
  'if(p.kind==="dust"){const dr=',
  'if(!isS&&p.kind==="galaxy"){const simpleCol=p.prism?prismShift(p.col,p.prismPhase+t*p.prismSpeed+phase*.18,twinkle,false):p.col;const simpleR=Math.max(.52,rad*.82);c.fillStyle=`rgba(${simpleCol[0]},${simpleCol[1]},${simpleCol[2]},${Math.min(.92,alpha*2.35)})`;c.fillRect(q.x-simpleR*.5,q.y-simpleR*.5,simpleR,simpleR);if(alpha>.24&&rad>.82){c.fillStyle=`rgba(${simpleCol[0]},${simpleCol[1]},${simpleCol[2]},${Math.min(.2,alpha*.42)})`;c.fillRect(q.x-simpleR*2.2,q.y-.21,simpleR*4.4,.42);c.fillRect(q.x-.21,q.y-simpleR*1.5,.42,simpleR*3)}continue}if(p.kind==="dust"){const dustR=Math.max(.5,rad*.9);c.fillStyle=`rgba(${p.col[0]},${p.col[1]},${p.col[2]},${Math.min(.36,alpha*1.7)})`;c.fillRect(q.x-dustR*.5,q.y-dustR*.5,dustR,dustR);continue}if(false&&p.kind==="dust"){const dr=',
];

const GALAXY_PROJECTION_CACHE_REPLACEMENTS: readonly Replacement[] = [
  [
    "let energy=0,particles=[],last=0,frameRAF=0;",
    "let energy=0,particles=[],last=0,frameRAF=0,projectionCache=[],rotCY=1,rotSY=0,rotCP=1,rotSP=0,rotCR=1,rotSR=0;",
  ],
  [
    "function project(p,yA,pA,rA,t=0){",
    "function project(p,yA,pA,rA,t=0,out={x:0,y:0,z:0,scale:0}){",
  ],
  [
    'const living=p.kind==="galaxy"||p.kind==="dust"||p.kind==="super"||p.kind==="event";const radial=living?Math.hypot(p.x,p.z):0,arm=living?Math.atan2(p.z,p.x):0,wave=living?Math.sin(t*55e-6+arm*1.65+radial*4.6):0,swirl=living?Math.sin(t*38e-6+radial*3.4)*.006:0,breath=living?wave*.014:0,px=p.x*(1+breath)-p.z*swirl,pz=p.z*(1+breath*.72)+p.x*swirl,py=p.y+(living?Math.cos(t*52e-6+arm*1.4)*(.008+radial*.004):0);const cy=Math.cos(yA),sy=Math.sin(yA),cp=Math.cos(pA),sp=Math.sin(pA),cr=Math.cos(rA),sr=Math.sin(rA),x1=px*cy-pz*sy,z1=px*sy+pz*cy,y1=py*cp-z1*sp,z2=py*sp+z1*cp,x2=x1*cr-y1*sr,y2=x1*sr+y1*cr,sc=1/(3.05+z2);',
    "const px=p.x,pz=p.z,py=p.y,cy=rotCY,sy=rotSY,cp=rotCP,sp=rotSP,cr=rotCR,sr=rotSR,x1=px*cy-pz*sy,z1=px*sy+pz*cy,y1=py*cp-z1*sp,z2=py*sp+z1*cp,x2=x1*cr-y1*sr,y2=x1*sr+y1*cr,sc=1/(3.05+z2);",
  ],
  [
    "return{x:W*.5+x2*minSide*1.34*sc,y:H*.5+y2*minSide*1.34*sc,z:z2,scale:sc}}",
    "out.x=W*.5+x2*minSide*1.34*sc;out.y=H*.5+y2*minSide*1.34*sc;out.z=z2;out.scale=sc;return out}",
  ],
  [
    "const proj=particles.map(p=>({p,q:project(p,yaw,pitch,roll,t)}));proj.sort((a,b)=>a.q.z-b.q.z);",
    "rotCY=Math.cos(yaw);rotSY=Math.sin(yaw);rotCP=Math.cos(pitch);rotSP=Math.sin(pitch);rotCR=Math.cos(roll);rotSR=Math.sin(roll);const proj=projectionCache;proj.length=particles.length;for(let i=0;i<particles.length;i++){const cached=proj[i]||(proj[i]={p:null,q:{x:0,y:0,z:0,scale:0}});cached.p=particles[i];project(cached.p,yaw,pitch,roll,t,cached.q)}proj.sort((a,b)=>a.q.z-b.q.z);",
  ],
] as const;

const ENTRY_REPLACEMENTS: readonly Replacement[] = [
  ["DPR=Math.min(devicePixelRatio||1,1.65)", "DPR=Math.min(devicePixelRatio||1,1.15)"],
  ["(mobile?680:1140)", "(mobile?440:760)"],
  ["(mobile?460:720)", "(mobile?250:440)"],
  ["(mobile?192:320)", "(mobile?72:124)"],
  ["(mobile?44:76)", "(mobile?20:34)"],
  [".slice(0,130)", ".slice(0,18)"],
  ...GALAXY_PROJECTION_CACHE_REPLACEMENTS,
  GALAXY_STAR_PAINT_REPLACEMENT,
  [
    "function frame(now){frameRAF=0;if(reduced||!shouldRenderGalaxy())return;if(!last)last=now-FRAME_MS;const rawDt=now-last;",
    "function frame(now){frameRAF=0;if(reduced||!shouldRenderGalaxy())return;if(!last)last=now-FRAME_MS;const minFrameGap=innerWidth<700?48:38;if(now-last<minFrameGap){scheduleFrame();return}const rawDt=now-last;",
  ],
] as const;

const UNIVERSE_REPLACEMENTS: readonly Replacement[] = [
  ["DPR=Math.min(devicePixelRatio||1,1.5)", "DPR=Math.min(devicePixelRatio||1,1)"],
  ["const PARTICLE_CAP=1880", "const PARTICLE_CAP=1120"],
  [
    "const density=mobile?{galaxy:620,far:430,dust:118,super:32}:{galaxy:900,far:585,dust:165,super:48}",
    "const density=mobile?{galaxy:360,far:210,dust:52,super:18}:{galaxy:640,far:330,dust:82,super:30}",
  ],
  ["const nodeBudget=innerWidth<700?54:82", "const nodeBudget=innerWidth<700?10:16"],
  ["if(profile.nebula>.48)drawNebula(t);", "if(false)drawNebula(t);"],
  [
    "if(farAlpha>.095&&farR>.7)spike(q.x,q.y,farR*2.4,farCol,Math.min(.12,farAlpha*.24),phase);continue",
    "continue",
  ],
  ...GALAXY_PROJECTION_CACHE_REPLACEMENTS,
  GALAXY_STAR_PAINT_REPLACEMENT,
  [
    "function frame(now){frameRAF=0;if(reduced||!shouldRenderGalaxy())return;if(!last)last=now-FRAME_MS;const rawDt=now-last;",
    "function frame(now){frameRAF=0;if(reduced||!shouldRenderGalaxy())return;if(!last)last=now-FRAME_MS;const minFrameGap=innerWidth<700?48:38;if(now-last<minFrameGap){scheduleFrame();return}const rawDt=now-last;",
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
