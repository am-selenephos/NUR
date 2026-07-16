export const V197_STAR_BRAIN_LIFECYCLE_PROFILE = "adaptive-lifecycle-v1";

type Replacement = readonly [from: string, to: string];

const REPLACEMENTS: readonly Replacement[] = [
  [
    `  resize();
  addEventListener('resize',resize,{passive:true});
  if(typeof ResizeObserver!=='undefined') new ResizeObserver(resize).observe(host);`,
    `  const lifecycleAbort=new AbortController();
  const lifecycleSignal=lifecycleAbort.signal;
  const deferredTimers=new Set();
  let disposed=false,renderVisible=true,renderRAF=0,pulseTimer=0,reducedFrameDrawn=false;
  let resizeObserver=null,visibilityObserver=null,surfaceObserver=null,modeObserver=null,sparkObserver=null;
  const defer=(callback,delay)=>{
    const id=setTimeout(()=>{deferredTimers.delete(id);if(!disposed)callback()},delay);
    deferredTimers.add(id);
    return id;
  };
  resize();
  const onResize=()=>{resize();scheduleRender(true)};
  addEventListener('resize',onResize,{passive:true,signal:lifecycleSignal});
  if(typeof ResizeObserver!=='undefined'){
    resizeObserver=new ResizeObserver(onResize);
    resizeObserver.observe(host);
  }`,
  ],
  [
    `    for(let i=0;i<n;i++) setTimeout(()=>firePulse(), Math.random()*420);`,
    `    for(let i=0;i<n;i++) defer(()=>firePulse(),Math.random()*420);`,
  ],
  [
    `  new MutationObserver(()=>{
    if(host.classList.contains('is-entry-absorbing')) absorb();
    else if(host.classList.contains('is-bursting') && mode==='live') shatter();
  }).observe(host,{attributes:true,attributeFilter:['class']});`,
    `  modeObserver=new MutationObserver(()=>{
    if(host.classList.contains('is-entry-absorbing')) absorb();
    else if(host.classList.contains('is-bursting') && mode==='live') shatter();
  });
  modeObserver.observe(host,{attributes:true,attributeFilter:['class']});`,
  ],
  [
    `  canvas.addEventListener('wheel',e=>{
    e.preventDefault();
    targetZoom=Math.max(.72,Math.min(1.5,targetZoom + (e.deltaY<0?.09:-.09)));
  },{passive:false});`,
    `  canvas.addEventListener('wheel',e=>{
    if(!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    targetZoom=Math.max(.72,Math.min(1.5,targetZoom + (e.deltaY<0?.09:-.09)));
  },{passive:false,signal:lifecycleSignal});`,
  ],
  [
    `  if(!REDUCED){
    setInterval(()=>{ if(mode==='live' && !document.hidden && pulses.length<9) firePulse(); }, 640);
  }

  /* ── 8) render loop: full stellar pipeline, adaptive quality ─────────── */
  let projected = new Array(pts.length);
  let emaDt=16, quality=2, lastNow=performance.now();
  function frame(now){
    requestAnimationFrame(frame);
    if(document.hidden) return;
    const welcome=document.getElementById('welcome');
    if(welcome && getComputedStyle(welcome).display==='none') return;`,
    `  /* ── 8) render loop: full stellar pipeline, adaptive quality ─────────── */
  let projected = new Array(pts.length);
  let emaDt=16, quality=2, lastNow=performance.now();
  const surfaceAvailable=()=>{
    const welcome=document.getElementById('welcome');
    return !welcome || getComputedStyle(welcome).display!=='none';
  };
  const canRender=()=>!disposed && !document.hidden && renderVisible && host.isConnected && surfaceAvailable();
  function stopRender(){
    if(renderRAF){cancelAnimationFrame(renderRAF);renderRAF=0}
  }
  function stopAmbientPulse(){
    if(pulseTimer){clearTimeout(pulseTimer);pulseTimer=0}
  }
  function scheduleAmbientPulse(){
    if(REDUCED || disposed || pulseTimer || !canRender()) return;
    pulseTimer=setTimeout(()=>{
      pulseTimer=0;
      if(mode==='live' && pulses.length<9) firePulse();
      scheduleAmbientPulse();
    },640);
  }
  function scheduleRender(force=false){
    if(disposed || renderRAF || document.hidden || !renderVisible || !host.isConnected) return;
    if((REDUCED && reducedFrameDrawn && !force) || (!force && !surfaceAvailable())) return;
    renderRAF=requestAnimationFrame(frame);
  }
  function refreshRuntimeActivity(){
    lastNow=performance.now();
    if(canRender()){
      scheduleRender();
      scheduleAmbientPulse();
      return;
    }
    stopRender();
    stopAmbientPulse();
  }
  function dispose(){
    if(disposed) return;
    disposed=true;
    stopRender();
    stopAmbientPulse();
    for(const id of deferredTimers) clearTimeout(id);
    deferredTimers.clear();
    resizeObserver?.disconnect();
    visibilityObserver?.disconnect();
    surfaceObserver?.disconnect();
    modeObserver?.disconnect();
    sparkObserver?.disconnect();
    lifecycleAbort.abort();
    host.classList.remove('is-grabbing');
    if(window.nurStarBrain) delete window.nurStarBrain;
    if(window.__nurV197) delete window.__nurV197;
  }
  function frame(now){
    renderRAF=0;
    if(!canRender()) return;
    if(REDUCED) reducedFrameDrawn=true;`,
  ],
  [
    `    if(!REDUCED && Math.random()<.30 && mode==='live'){
      const i=(Math.random()*pts.length)|0;
      const q=projected[i];
      if(q && q.z>-.2) emitMote(pts[i],q.x,q.y);
    }
  }
  requestAnimationFrame(frame);`,
    `    if(!REDUCED && Math.random()<.30 && mode==='live'){
      const i=(Math.random()*pts.length)|0;
      const q=projected[i];
      if(q && q.z>-.2) emitMote(pts[i],q.x,q.y);
    }
    if(!REDUCED) scheduleRender();
  }
  document.addEventListener('visibilitychange',refreshRuntimeActivity,{passive:true,signal:lifecycleSignal});
  addEventListener('pagehide',dispose,{once:true,signal:lifecycleSignal});
  if(typeof IntersectionObserver!=='undefined'){
    visibilityObserver=new IntersectionObserver(entries=>{
      const entry=entries[entries.length-1];
      renderVisible=Boolean(entry?.isIntersecting && entry.intersectionRatio>0);
      refreshRuntimeActivity();
    },{threshold:[0,.01]});
    visibilityObserver.observe(host);
  }
  const welcomeSurface=document.getElementById('welcome');
  if(welcomeSurface){
    surfaceObserver=new MutationObserver(refreshRuntimeActivity);
    surfaceObserver.observe(welcomeSurface,{attributes:true,attributeFilter:['class','style']});
  }
  scheduleRender(true);
  scheduleAmbientPulse();`,
  ],
  [
    `  if(!REDUCED && !document.getElementById('v197-sparkfield')){`,
    `  if(false){`,
  ],
  [
    `  new MutationObserver(muts=>{
    for(const mu of muts){`,
    `  sparkObserver=new MutationObserver(muts=>{
    for(const mu of muts){`,
  ],
  [
    `  }).observe(document.body,{childList:true,subtree:true});

  /* debug handle */`,
    `  });
  sparkObserver.observe(document.body,{childList:true,subtree:true});

  /* debug handle */`,
  ],
  [
    `    get quality(){return quality},
    canvas
  };`,
    `    get quality(){return quality},
    get frameTime(){return emaDt},
    get running(){return renderRAF!==0},
    canvas,
    dispose
  };`,
  ],
] as const;

export type V197StarBrainLifecycleResult = {
  source: string;
  applied: boolean;
  replacementCount: number;
  failure?: string;
};

export function applyV197StarBrainLifecycleProfile(source: string): V197StarBrainLifecycleResult {
  let profiled = source;

  for (const [index, [from, to]] of REPLACEMENTS.entries()) {
    const first = profiled.indexOf(from);
    if (first < 0) {
      return { source, applied: false, replacementCount: 0, failure: `missing:${index}` };
    }
    if (profiled.indexOf(from, first + from.length) >= 0) {
      return { source, applied: false, replacementCount: 0, failure: `duplicate:${index}` };
    }
    profiled = `${profiled.slice(0, first)}${to}${profiled.slice(first + from.length)}`;
  }

  return {
    source: profiled,
    applied: true,
    replacementCount: REPLACEMENTS.length,
  };
}
