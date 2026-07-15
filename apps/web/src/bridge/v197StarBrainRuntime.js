
(() => {
  'use strict';
  const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const host = document.getElementById('front-nur-star');
  if(!host) return;

  /* ── 1) retire the V7 renderer without touching its code ─────────────
     Starve its canvas: 0×0 + detached ⇒ every old draw call is a no-op,
     its loop's guards keep it idle-cheap. Later layers win; earlier stay. */
  const legacy = document.getElementById('nur-brain-canvas');
  if(legacy){
    try{ legacy.width = 0; legacy.height = 0; }catch(e){}
    legacy.style.display = 'none';
    legacy.removeAttribute('id');
    if(legacy.parentNode) legacy.parentNode.removeChild(legacy);
  }

  /* ── 2) nebula veil: halve ONLY full-screen wash fills on #space3d ────
     drawNebula paints all 7 washes with fillRect(0,0,W,H); stars use arcs
     and star paths. Instance-level patch — the galaxy source is untouched,
     star brightness untouched, washes at ~50%: faint nebula, depth kept. */
  (function(){
    const space = document.getElementById('space3d');
    if(!space) return;
    const sc = space.getContext('2d');
    if(!sc || sc.__v197Veil) return;
    sc.__v197Veil = true;
    const orig = sc.fillRect;
    sc.fillRect = function(x,y,w,h){
      if(x===0 && y===0 && w>innerWidth*.92 && h>innerHeight*.92){
        const ga = this.globalAlpha;
        this.globalAlpha = ga*.5;
        orig.call(this,x,y,w,h);
        this.globalAlpha = ga;
        return;
      }
      orig.call(this,x,y,w,h);
    };
  })();

  host.setAttribute('title','drag to spin the mind - click: it dissolves into stardust and reforms - double-click: neural storm - scroll to zoom');
  host.setAttribute('aria-label','A living brain made of real stars. Drag to spin it. Click and it dissolves into star glitter, then flows back together.');

  const canvas = document.createElement('canvas');
  canvas.id = 'nur-brain-canvas-v197';
  host.appendChild(canvas);
  const c = canvas.getContext('2d', { alpha:true });

  const rnd=(a,b)=>a+Math.random()*(b-a);
  const pick=arr=>arr[(Math.random()*arr.length)|0];
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

  /* ── 3) EXACT galaxy stellar pipeline port — no shortcuts ─────────────
     SPEC / DIST / rndCol / NUR_RAINBOW / prismShift / mixCol / scintCol /
     stellarPath / glitterShard / starGlow / spike copied verbatim from
     nur-v43-galaxy-extracted; only the ctx binding (c) is this canvas. */
  const SPEC = {
    O:  [[140,160,255],[158,178,255],[118,148,255]],
    B:  [[172,192,255],[192,208,255],[162,185,255]],
    A:  [[250,253,255],[255,255,255],[244,251,255]],
    F:  [[255,252,215],[252,248,200],[255,250,188]],
    G:  [[255,244,164],[255,238,138],[255,230,118]],
    K:  [[255,210,78],[255,195,62],[255,178,48]],
    M:  [[255,152,98],[255,130,68],[255,108,56]],
    Nb: [[78,158,255],[98,178,255],[58,138,220]],
    Nr: [[255,78,98],[218,58,78],[198,48,68]],
    Ng: [[78,218,168],[58,198,148],[68,208,158]]
  };
  const DIST = [
    {t:'M',w:.30},{t:'K',w:.20},{t:'G',w:.16},{t:'F',w:.12},
    {t:'A',w:.10},{t:'B',w:.08},{t:'O',w:.04}
  ];
  function rndCol(bright=false){
    if(bright){
      const bt=['G','G','K','K','F','M','A','B','O'];
      const t=bt[(Math.random()*bt.length)|0];
      return SPEC[t][(Math.random()*SPEC[t].length)|0];
    }
    let r=Math.random(),cum=0;
    for(const {t,w} of DIST){cum+=w;if(r<cum)return SPEC[t][(Math.random()*SPEC[t].length)|0]}
    return SPEC.G[0];
  }
  const NUR_RAINBOW=[
    [255,108,128],[255,158,74],[255,222,92],[126,237,130],
    [99,224,255],[121,151,255],[194,138,255],[255,142,211]
  ];
  function mixCol(a,b,t){
    return [
      Math.round(a[0]+(b[0]-a[0])*t),
      Math.round(a[1]+(b[1]-a[1])*t),
      Math.round(a[2]+(b[2]-a[2])*t)
    ];
  }
  function prismShift(col,phase,twinkle=1,isS=false){
    const wheel=NUR_RAINBOW;
    const orbit=((phase%(Math.PI*2))+(Math.PI*2))/(Math.PI*2)*wheel.length;
    const i0=Math.floor(orbit)%wheel.length;
    const i1=(i0+1)%wheel.length;
    const t=orbit-i0;
    const prism=mixCol(wheel[i0],wheel[i1],t);
    const amt=(isS?.34:.24)+twinkle*(isS?.18:.10);
    return mixCol(col,prism,Math.min(.58,amt));
  }
  function scintCol(col,phase,twinkle,isS){
    const whiteAmt=(isS?.18:.06)+twinkle*(isS?.16:.04);
    return mixCol(col,[255,250,228],whiteAmt);
  }
  function stellarPath(x,y,outer,inner,points=4,rot=-Math.PI/2){
    c.beginPath();
    for(let i=0;i<points*2;i++){
      const rr=i%2===0?outer:inner;
      const a=rot+i*Math.PI/points;
      const px=x+Math.cos(a)*rr;
      const py=y+Math.sin(a)*rr;
      if(i===0)c.moveTo(px,py);else c.lineTo(px,py);
    }
    c.closePath();
  }
  function glitterShard(x,y,len,col,a,rot){
    c.save();c.translate(x,y);c.rotate(rot);
    const g=c.createLinearGradient(-len,0,len,0);
    g.addColorStop(0,`rgba(${col[0]},${col[1]},${col[2]},0)`);
    g.addColorStop(.46,`rgba(${col[0]},${col[1]},${col[2]},${a*.42})`);
    g.addColorStop(.5,`rgba(255,250,220,${a})`);
    g.addColorStop(.54,`rgba(${col[0]},${col[1]},${col[2]},${a*.42})`);
    g.addColorStop(1,`rgba(${col[0]},${col[1]},${col[2]},0)`);
    c.strokeStyle=g;c.lineWidth=.48;
    c.beginPath();c.moveTo(-len,0);c.lineTo(len,0);c.stroke();
    c.rotate(Math.PI/2);
    c.globalAlpha*=.78;
    c.beginPath();c.moveTo(-len*.42,0);c.lineTo(len*.42,0);c.stroke();
    c.restore();
  }
  function starGlow(x,y,r,col,alpha,twinkle,isS,phase=0){
    const sCol=scintCol(col,phase,twinkle,isS);
    const hR=r*(isS?5.8:3.15);
    const hg=c.createRadialGradient(x,y,r*.45,x,y,hR);
    hg.addColorStop(0,`rgba(${sCol[0]},${sCol[1]},${sCol[2]},${alpha*0.10*twinkle})`);
    hg.addColorStop(0.32,`rgba(${sCol[0]},${sCol[1]},${sCol[2]},${alpha*0.036})`);
    hg.addColorStop(1,`rgba(${sCol[0]},${sCol[1]},${sCol[2]},0)`);
    c.fillStyle=hg;c.beginPath();c.arc(x,y,hR,0,Math.PI*2);c.fill();

    const bodyR=isS?clamp(r*.18,2.4,7.2):clamp(r*.12,1.05,2.95);
    const innerR=Math.max(.18,bodyR*.105);
    const rot=phase*.37+(twinkle*.82)+(isS?Math.PI/8:0);
    glitterShard(x,y,bodyR*(isS?5.8:3.6),sCol,Math.min(.30,alpha*1.55),rot);
    glitterShard(x,y,bodyR*(isS?3.0:2.1),sCol,Math.min(.14,alpha*1.0),rot+Math.PI/4);
    const ig=c.createRadialGradient(x,y,0,x,y,bodyR);
    ig.addColorStop(0,   `rgba(255,252,226,${Math.min(.96,alpha*twinkle*4.5)})`);
    ig.addColorStop(0.22,`rgba(${sCol[0]},${sCol[1]},${sCol[2]},${Math.min(.78,alpha*twinkle*1.9)})`);
    ig.addColorStop(0.64,`rgba(${sCol[0]},${sCol[1]},${sCol[2]},${Math.min(.20,alpha*.56)})`);
    ig.addColorStop(1,   `rgba(${sCol[0]},${sCol[1]},${sCol[2]},0)`);
    c.fillStyle=ig;stellarPath(x,y,bodyR,innerR,4,rot-Math.PI/2);c.fill();
    c.strokeStyle=`rgba(255,250,220,${Math.min(.38,alpha*1.8)})`;
    c.lineWidth=.42;stellarPath(x,y,bodyR*.78,innerR*.78,4,rot-Math.PI/2);c.stroke();

    const cA=Math.min(alpha*twinkle*5.0,0.96);
    if(cA>0.04){
      const wr=Math.min(255,sCol[0]+45),wg=Math.min(255,sCol[1]+38),wb=Math.min(255,sCol[2]+28);
      c.fillStyle=`rgba(${wr},${wg},${wb},${cA})`;
      stellarPath(x,y,Math.max(.95,bodyR*.24+twinkle*.35),Math.max(.20,bodyR*.045),4,rot);
      c.fill();
    }

    if(alpha>.08 && twinkle>.92){
      const shards=isS?5:2;
      for(let i=0;i<shards;i++){
        const a=rot+i*(Math.PI*2/shards)+Math.sin(twinkle+i)*.15;
        const rr=bodyR*rnd(1.08,1.72);
        glitterShard(x+Math.cos(a)*rr,y+Math.sin(a)*rr,rnd(1.6,3.8)*(isS?1.5:1),sCol,Math.min(.24,alpha),a+Math.PI/2);
      }
    }
  }
  function spike(x,y,len,col,a,rot=0){
    c.save();c.translate(x,y);c.rotate(rot);
    const drawS=(l,angle,opFrac)=>{
      c.rotate(angle);
      const sg=c.createLinearGradient(-l,0,l,0);
      sg.addColorStop(0,  `rgba(${Math.min(255,col[0]+25)},${Math.min(255,col[1]+15)},255,0)`);
      sg.addColorStop(0.26,`rgba(${col[0]},${col[1]},${col[2]},${a*opFrac*.44})`);
      sg.addColorStop(0.5, `rgba(255,255,${Math.min(255,col[2]+65)},${a*opFrac*.82})`);
      sg.addColorStop(0.74,`rgba(${col[0]},${col[1]},${col[2]},${a*opFrac*.44})`);
      sg.addColorStop(1,  `rgba(${Math.min(255,col[0]+25)},${Math.min(255,col[1]+15)},255,0)`);
      c.strokeStyle=sg;c.lineWidth=0.55;
      c.beginPath();c.moveTo(-l,0);c.lineTo(l,0);c.stroke();
      c.rotate(-angle);
    };
    drawS(len*.54,0,.62);
    drawS(len*.54,Math.PI/2,.62);
    c.restore();
  }

  /* ── 4) anatomy: layered point cloud — volume, not shell ─────────────
     axes: x = left/right (hemispheres), y = up, z = front(+)/back(−) */
  const MOBILE   = innerWidth < 700;
  const N_CORTEX = MOBILE ? 430 : 640;
  const N_DEEP   = MOBILE ? 140 : 220;
  const N_CEREB  = MOBILE ? 96  : 140;
  const N_STEM   = MOBILE ? 20  : 28;
  const N_CAL    = MOBILE ? 22  : 32;
  const GOLD_SET = [[245,214,123],[255,233,168],[255,244,190]];
  const pts = [];

  function addPoint(x,y,z,group,lum,opts){
    opts = opts||{};
    const bright = opts.bright ?? (group==='cortex' && Math.random()<.10);
    pts.push({
      x,y,z, group, bright,
      ox:0, oy:0, oz:0, vx:0, vy:0, vz:0,
      r: opts.r ?? rnd(.7,2.1)*(group==='stem'?.8:1),
      col: opts.col || rndCol(bright),
      prism: opts.prism ?? (group==='cortex' ? Math.random()<.18 : Math.random()<.08),
      prismPhase: rnd(0,Math.PI*2), prismSpeed: rnd(.00012,.00042),
      phase: rnd(0,Math.PI*2),
      twinkAmt: bright?rnd(.05,.14):rnd(.10,.30),
      twinkSpd: rnd(.00055,.00225),
      twinkPh: rnd(0,Math.PI*2),
      flashP: bright?0.99925:0.9987,
      lum: clamp(lum,0.05,1.25)
    });
  }

  /* multi-octave gyri fold field: >0 crest, <0 sulcus */
  function foldField(az,inc){
    return .052*Math.sin(az*7 + Math.sin(inc*4)*1.8)
         + .030*Math.sin(az*13 + inc*9)
         + .016*Math.sin(az*21 - inc*13.5);
  }

  /* cortex surface: golden-spiral sphere → hemispheres with real features */
  for(let i=0;i<N_CORTEX;i++){
    const t=(i+.5)/N_CORTEX;
    const inc=Math.acos(1-2*t), az=Math.PI*(1+Math.sqrt(5))*i;
    let x=Math.sin(inc)*Math.cos(az), y=Math.cos(inc), z=Math.sin(inc)*Math.sin(az);
    let fold = foldField(az,inc);
    let lum  = fold>0 ? Math.min(1.22, 1+fold*3.2) : Math.max(.55, 1+fold*5.5);

    // central sulcus: crown groove, upper end posterior
    const cs = Math.abs(z - (.06 - y*.26));
    if(cs<.05 && y>.12 && Math.abs(x)>.14){ fold=-.075; lum=Math.min(lum,.52); }

    // lateral (Sylvian) fissure + temporal-lobe bulge below it
    const syl = y - (-.18 + z*.16);
    if(Math.abs(syl)<.055 && Math.abs(x)>.42 && z>-.42 && z<.82){
      fold=-.09; lum=Math.min(lum,.46);
    } else if(syl<-.055 && syl>-.52 && Math.abs(x)>.38 && z>-.30 && z<.72){
      x*=1.055; y-=.045; lum*=1.04;
    }

    const f=1+fold;
    x*=f; y*=f; z*=f;
    x*=1.00; y*=.84; z*=1.27;

    // longitudinal fissure: hemispheres apart at the midline
    if(Math.abs(x)<.11 && y>-.12){
      x=Math.sign(x||rnd(-1,1))*(.11+Math.abs(x)*.35);
      lum=Math.min(lum,.55);
    }
    // frontal taper + flattened underside
    if(z>.62) x*=1-.16*(z-.62);
    if(y<-.44) y=-.44+(y+.44)*.45;
    addPoint(x,y,z,'cortex',lum);
  }

  /* subsurface volume: dim interior stars — the mind reads as a solid */
  function normal(){
    let u=0,v=0;
    while(u===0)u=Math.random();
    while(v===0)v=Math.random();
    return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);
  }
  for(let i=0;i<N_DEEP;i++){
    let dx=normal(),dy=normal(),dz=normal();
    const m=Math.hypot(dx,dy,dz)||1; dx/=m;dy/=m;dz/=m;
    const rr=.12+Math.cbrt(Math.random())*.68;
    let x=dx*rr*1.0, y=dy*rr*.84, z=dz*rr*1.27;
    if(Math.abs(x)<.06 && y>0) x=Math.sign(x||(Math.random()-.5))*.06;
    if(y<-.42) y=-.42+(y+.42)*.5;
    addPoint(x,y,z,'deep',rnd(.34,.58),{r:rnd(.45,1.15),bright:false,prism:false});
  }

  /* cerebellum: finely foliated small ellipsoid, lower back + vermis groove */
  for(let i=0;i<N_CEREB;i++){
    const t=(i+.5)/N_CEREB;
    const inc=Math.acos(1-2*t), az=Math.PI*(1+Math.sqrt(5))*i;
    let x=Math.sin(inc)*Math.cos(az), y=Math.cos(inc), z=Math.sin(inc)*Math.sin(az);
    const stripe=Math.sin(inc*17);
    const f=1+.035*stripe;
    let lum=(.62+.38*(0.5+0.5*stripe))*.96;
    if(Math.abs(x)<.09) lum*=.8;                    // vermis midline
    addPoint(x*.56*f, -.56+y*.30*f, -.84+z*.44*f, 'cereb', lum, {r:rnd(.6,1.6)});
  }

  /* brainstem: tapering column, gentle forward tilt */
  for(let i=0;i<N_STEM;i++){
    const t=i/N_STEM, a=rnd(0,Math.PI*2);
    const rr=(0.10-t*.045)*Math.sqrt(rnd(0,1));
    addPoint(Math.cos(a)*rr, -.40-t*.52, -.28+t*.20+Math.sin(a)*rr, 'stem', .78, {r:rnd(.55,1.5)});
  }

  /* corpus callosum: faint gold arc bridging the hemispheres */
  for(let i=0;i<N_CAL;i++){
    const t=(i+.5)/N_CAL;
    const a=-.35+t*(Math.PI+.80)+rnd(-.04,.04);
    const px=rnd(-.028,.028);
    const py=.03+Math.sin(a)*.235;
    const pz=-.05+Math.cos(a)*.40;
    addPoint(px,py,pz,'cal',rnd(.42,.62),{r:rnd(.5,1.05),col:pick(GOLD_SET),bright:false,prism:false});
  }

  /* ── 5) synapse web: k-nearest within tissue ─────────────────────────── */
  const LINKABLE = p => p.group==='cortex'||p.group==='cereb'||p.group==='stem';
  const edges=[]; const adj=pts.map(()=>[]);
  const edgeSet=new Set();
  for(let i=0;i<pts.length;i++){
    if(!LINKABLE(pts[i])) continue;
    let n1=-1,n2=-1,d1=9,d2=9;
    for(let j=0;j<pts.length;j++){
      if(i===j || pts[i].group!==pts[j].group) continue;
      const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y, dz=pts[i].z-pts[j].z;
      const d=dx*dx+dy*dy+dz*dz;
      if(d<d1){d2=d1;n2=n1;d1=d;n1=j}else if(d<d2){d2=d;n2=j}
    }
    for(const [j,dd] of [[n1,d1],[n2,d2]]){
      if(j<0 || dd>.09) continue;
      const key=i<j?i+'-'+j:j+'-'+i;
      if(!edgeSet.has(key)){
        edgeSet.add(key);
        edges.push({key,a:i,b:j});
        adj[i].push(j); adj[j].push(i);
      }
    }
  }

  /* ── 6) neural pulses along the synapses ─────────────────────────────── */
  const PULSE_COLS=[[78,218,168],[78,218,168],[78,158,255],[245,214,123],[255,108,128]];
  const pulses=[];
  function firePulse(from){
    const start = from ?? (Math.random()*pts.length)|0;
    if(!adj[start] || !adj[start].length) return;
    const path=[start]; let cur=start;
    for(let h=0;h<3+((Math.random()*4)|0);h++){
      const next=adj[cur][(Math.random()*adj[cur].length)|0];
      if(next==null) break;
      path.push(next); cur=next;
    }
    if(path.length>1) pulses.push({path, t:0, speed:rnd(.028,.05), col:pick(PULSE_COLS)});
  }

  /* glitter motes drifting off the surface */
  const motes=[];
  function emitMote(p, px, py){
    if(motes.length>44) return;
    motes.push({x:px, y:py, vx:rnd(-.22,.22), vy:rnd(-.5,-.14), life:rnd(38,80), max:80,
                col:p?p.col:pick(GOLD_SET), r:rnd(.6,1.6)});
  }

  /* ── 7) camera / interaction / modes (5D kept, tuned) ────────────────── */
  let W=0,H=0,cx=0,cy=0,scale=1,DPR=1;
  let yaw=.85, pitch=-.14, vyaw=REDUCED?0:.0022, vpitch=0;
  let zoom=1, targetZoom=1;
  let dragging=false, dragDist=0, lx=0, ly=0;
  let hoverX=-1e4, hoverY=-1e4;
  let mode='live', modeT=0;
  let energy=0;
  let breath=0;

  function resize(){
    DPR=Math.min(devicePixelRatio||1,1.5);
    const r=host.getBoundingClientRect();
    W=Math.max(2,r.width); H=Math.max(2,r.height);
    canvas.width=Math.round(W*DPR); canvas.height=Math.round(H*DPR);
    c.setTransform(DPR,0,0,DPR,0,0);
    cx=W/2; cy=H/2; scale=Math.min(W,H)*.34;
  }
  resize();
  addEventListener('resize',resize,{passive:true});
  if(typeof ResizeObserver!=='undefined') new ResizeObserver(resize).observe(host);

  function project(p){
    const X=p.x+p.ox, Y=p.y+p.oy, Z=p.z+p.oz;
    const cyw=Math.cos(yaw), syw=Math.sin(yaw);
    const cp=Math.cos(pitch), sp=Math.sin(pitch);
    const x1=X*cyw - Z*syw, z1=X*syw + Z*cyw;
    const y1=Y*cp - z1*sp,  z2=Y*sp + z1*cp;
    const sc=1/(2.7 - z2*.62);
    return { x:cx + x1*scale*zoom*sc*1.55, y:cy - y1*scale*zoom*sc*1.55, z:z2, sc };
  }

  function storm(power=1){
    energy=Math.min(1.6, energy+power);
    const n=Math.round(10+16*power);
    for(let i=0;i<n;i++) setTimeout(()=>firePulse(), Math.random()*420);
    for(const p of pts){
      const m=Math.hypot(p.x,p.y,p.z)||1;
      const k=.028*power;
      p.vx+=p.x/m*k*rnd(.4,1); p.vy+=p.y/m*k*rnd(.4,1); p.vz+=p.z/m*k*rnd(.4,1);
    }
  }
  function absorb(){ mode='absorb'; modeT=0; }
  function shatter(){
    if(mode==='shatter' || mode==='reform') return;
    mode='shatter'; modeT=0;
    pulses.length=0;
    energy=Math.min(1.6, energy+1);
    for(const p of pts){
      const m=Math.hypot(p.x,p.y,p.z)||1;
      const s=rnd(.055,.16);
      p.vx += p.x/m*s + rnd(-.045,.045);
      p.vy += p.y/m*s + rnd(-.045,.045) + .015;
      p.vz += p.z/m*s + rnd(-.045,.045);
    }
    for(let i=0;i<28;i++){
      const q=projected[(Math.random()*pts.length)|0];
      if(q) emitMote(null,q.x,q.y);
    }
  }
  window.nurStarBrain={ storm, absorb, shatter, firePulse };

  new MutationObserver(()=>{
    if(host.classList.contains('is-entry-absorbing')) absorb();
    else if(host.classList.contains('is-bursting') && mode==='live') shatter();
  }).observe(host,{attributes:true,attributeFilter:['class']});

  canvas.addEventListener('pointerdown',e=>{
    dragging=true; dragDist=0; lx=e.clientX; ly=e.clientY;
    host.classList.add('is-grabbing');
    try{canvas.setPointerCapture(e.pointerId)}catch(err){}
    e.stopPropagation();
  });
  canvas.addEventListener('pointermove',e=>{
    const r=canvas.getBoundingClientRect();
    hoverX=e.clientX-r.left; hoverY=e.clientY-r.top;
    if(!dragging) return;
    const dx=e.clientX-lx, dy=e.clientY-ly;
    dragDist+=Math.abs(dx)+Math.abs(dy);
    lx=e.clientX; ly=e.clientY;
    vyaw = dx*.0032; vpitch = dy*.0026;
    yaw+=vyaw; pitch=Math.max(-1.1,Math.min(1.1,pitch+vpitch));
  });
  const endDrag=()=>{ if(!dragging) return; dragging=false; host.classList.remove('is-grabbing'); };
  canvas.addEventListener('pointerup',endDrag);
  canvas.addEventListener('pointercancel',endDrag);
  canvas.addEventListener('pointerleave',()=>{hoverX=hoverY=-1e4;});
  canvas.addEventListener('click',e=>{
    if(dragDist>7){ e.stopPropagation(); return; }
    // host's V4 click ritual adds .is-bursting → observer → shatter
  });
  canvas.addEventListener('wheel',e=>{
    e.preventDefault();
    targetZoom=Math.max(.72,Math.min(1.5,targetZoom + (e.deltaY<0?.09:-.09)));
  },{passive:false});
  canvas.addEventListener('dblclick',e=>{ e.stopPropagation(); storm(1.4); });

  if(!REDUCED){
    setInterval(()=>{ if(mode==='live' && !document.hidden && pulses.length<9) firePulse(); }, 640);
  }

  /* ── 8) render loop: full stellar pipeline, adaptive quality ─────────── */
  let projected = new Array(pts.length);
  let emaDt=16, quality=2, lastNow=performance.now();
  function frame(now){
    requestAnimationFrame(frame);
    if(document.hidden) return;
    const welcome=document.getElementById('welcome');
    if(welcome && getComputedStyle(welcome).display==='none') return;
    if(W<10){ resize(); if(W<10) return; }

    const dt=Math.min(50,now-lastNow); lastNow=now;
    emaDt+=(dt-emaDt)*.05;
    quality = emaDt>26 ? 0 : emaDt>19 ? 1 : 2;

    breath += .012;
    energy *= .965;
    zoom += (targetZoom-zoom)*.08;
    if(!dragging && !REDUCED){
      vyaw += (.0022 - vyaw)*.02;
      vpitch *= .92;
      yaw += vyaw; pitch = Math.max(-1.1,Math.min(1.1,pitch+vpitch))*.996;
    }

    let squeeze=1, cohesion=1, springK=.06, dampK=.86;
    if(mode==='absorb'){
      modeT++; squeeze=1-Math.min(.5,modeT*.032);
      if(modeT>24){ mode='bloom'; modeT=0; storm(1.5); }
    } else if(mode==='bloom'){
      modeT++; squeeze=.5+Math.min(.5,modeT*.05);
      if(modeT>34) mode='live';
    } else if(mode==='shatter'){
      modeT++; springK=.0022; dampK=.986;
      cohesion=Math.max(0,1-modeT*.055);
      if(modeT>80){ mode='reform'; modeT=0; }
    } else if(mode==='reform'){
      modeT++; springK=.026; dampK=.885;
      cohesion=Math.min(1,modeT*.018);
      if(modeT>95) mode='live';
    }

    for(const p of pts){
      p.vx+=-springK*p.ox; p.vy+=-springK*p.oy; p.vz+=-springK*p.oz;
      p.vx*=dampK; p.vy*=dampK; p.vz*=dampK;
      p.ox+=p.vx; p.oy+=p.vy; p.oz+=p.vz;
    }

    c.clearRect(0,0,W,H);

    /* aurora core glow behind the mind: teal → nebula blue → champagne */
    const g=c.createRadialGradient(cx,cy,0,cx,cy,scale*1.55);
    g.addColorStop(0,  `rgba(78,218,168,${.055+energy*.05})`);
    g.addColorStop(.42,`rgba(78,158,255,${.024+energy*.028})`);
    g.addColorStop(.72,`rgba(245,214,123,${.015+energy*.018})`);
    g.addColorStop(1,'rgba(0,0,0,0)');
    c.fillStyle=g; c.fillRect(0,0,W,H);

    const bob = REDUCED?0:Math.sin(breath*.7)*.02;
    for(let i=0;i<pts.length;i++){
      const p=pts[i];
      const bx=p.x, by=p.y, bz=p.z;
      p.x*=squeeze; p.y=p.y*squeeze+bob; p.z*=squeeze;
      projected[i]=project(p);
      p.x=bx; p.y=by; p.z=bz;
    }

    /* synapse web: teal, gold-lifting with storm energy */
    if(cohesion>.06){
      c.lineWidth=.55;
      const er=78+Math.round(energy*100), eg=218-Math.round(energy*4), eb=168-Math.round(energy*24);
      for(const e of edges){
        const A=projected[e.a], B=projected[e.b];
        const depth=(A.z+B.z)*.5;
        const al=(.05+Math.max(0,depth)*.075)*(1+energy*.8)*cohesion;
        if(al<.03) continue;
        c.strokeStyle=`rgba(${er},${eg},${eb},${Math.min(.22,al)})`;
        c.beginPath(); c.moveTo(A.x,A.y); c.lineTo(B.x,B.y); c.stroke();
      }
    }

    /* stars, back-to-front — full galaxy pipeline */
    const order=[...pts.keys()].sort((a,b)=>projected[a].z-projected[b].z);
    const deepSkip = quality===0;
    for(const i of order){
      const p=pts[i], q=projected[i];
      const cheap = p.group==='deep' || p.group==='cal';
      if(cheap && deepSkip && (i%2===(0|(now/500))%2)) continue;

      const twinkle=1-p.twinkAmt+p.twinkAmt*(.5+.5*Math.sin(now*p.twinkSpd+p.twinkPh));
      const flash=Math.random()>p.flashP?1.72:1;
      const lit=.40+.60*clamp((q.z+.9)/1.7,0,1);
      let a=(.26+.74*lit)*twinkle*flash*p.lum*(1+energy*.55)*(.35+.65*cohesion);

      const hd=Math.hypot(q.x-hoverX,q.y-hoverY);
      if(hd<58){
        const k=1-hd/58;
        a*=1+.9*k;
        p.vx+=(p.x)*.0016*k; p.vy+=(p.y)*.0016*k; p.vz+=(p.z)*.0016*k;
        if(Math.random()<.05*k) emitMote(p,q.x,q.y);
      }
      a=Math.min(1,a);
      if(a<.02) continue;

      const r=Math.max(.55,p.r*q.sc*2.55*zoom*(.62+.38*cohesion));
      if(cohesion<1) p.twinkPh+=p.twinkSpd*(1-cohesion)*22;
      const isS=p.bright;
      const phase=p.phase+now*.00024;
      const baseCol=p.prism
        ? prismShift(p.col,p.prismPhase+now*p.prismSpeed+phase*.18,twinkle,isS)
        : p.col;

      if(cheap){
        /* subsurface / callosum: soft volumetric glow, no crystal body */
        const dr=Math.max(1.4,r*2.3);
        const dg=c.createRadialGradient(q.x,q.y,0,q.x,q.y,dr*2.6);
        dg.addColorStop(0,`rgba(${baseCol[0]},${baseCol[1]},${baseCol[2]},${Math.min(.34,a*.34)})`);
        dg.addColorStop(.5,`rgba(${baseCol[0]},${baseCol[1]},${baseCol[2]},${Math.min(.10,a*.10)})`);
        dg.addColorStop(1,`rgba(${baseCol[0]},${baseCol[1]},${baseCol[2]},0)`);
        c.fillStyle=dg;c.beginPath();c.arc(q.x,q.y,dr*2.6,0,Math.PI*2);c.fill();
        c.fillStyle=`rgba(${baseCol[0]},${baseCol[1]},${baseCol[2]},${Math.min(.5,a*.9)})`;
        c.beginPath();c.arc(q.x,q.y,Math.max(.5,r*.62),0,Math.PI*2);c.fill();
        continue;
      }

      const renderCol=scintCol(baseCol,phase,twinkle,isS);
      const sR=Math.max(isS?5.6:2.75,r*(isS?4.0:2.05));
      starGlow(q.x,q.y,sR,baseCol,a*(isS?.40:.30),twinkle,isS,phase);

      if(quality>0 && (isS||(a>.30&&r>1.15))){
        const sl=Math.max(7,sR*(isS?5.4:2.9));
        spike(q.x,q.y,sl,renderCol,Math.min(.30,a*(isS?.34:.16)),p.twinkPh+now*.00007);
      }

      const cA=Math.min(.96,a*3.2);
      if(cA>0.02){
        c.fillStyle=`rgba(${renderCol[0]},${renderCol[1]},${renderCol[2]},${cA})`;
        stellarPath(q.x,q.y,Math.max(.62,r*.68),Math.max(.12,r*.10),4,p.twinkPh+now*.0004);
        c.fill();
      }
    }

    /* travelling neural pulses */
    for(let i=pulses.length-1;i>=0;i--){
      const pu=pulses[i];
      pu.t+=pu.speed;
      const seg=Math.floor(pu.t), f=pu.t-seg;
      if(seg>=pu.path.length-1){ pulses.splice(i,1); continue; }
      const A=projected[pu.path[seg]], B=projected[pu.path[seg+1]];
      const x=A.x+(B.x-A.x)*f, y=A.y+(B.y-A.y)*f;
      const [cr,cg,cb]=pu.col;
      c.strokeStyle=`rgba(${cr},${cg},${cb},.5)`;
      c.lineWidth=1.1;
      c.beginPath(); c.moveTo(A.x,A.y); c.lineTo(x,y); c.stroke();
      const pg=c.createRadialGradient(x,y,0,x,y,7);
      pg.addColorStop(0,`rgba(255,252,232,.95)`);
      pg.addColorStop(.3,`rgba(${cr},${cg},${cb},.75)`);
      pg.addColorStop(1,'rgba(0,0,0,0)');
      c.fillStyle=pg; c.beginPath(); c.arc(x,y,7,0,Math.PI*2); c.fill();
    }

    /* drifting glitter motes */
    for(let i=motes.length-1;i>=0;i--){
      const m=motes[i];
      m.x+=m.vx; m.y+=m.vy; m.life--;
      if(m.life<=0){ motes.splice(i,1); continue; }
      const ma=(m.life/m.max)*.8;
      const [cr,cg,cb]=m.col;
      c.fillStyle=`rgba(${cr},${cg},${cb},${ma})`;
      stellarPath(m.x,m.y,m.r+.6,Math.max(.14,(m.r+.6)*.3),4,m.life*.2);
      c.fill();
    }

    if(!REDUCED && Math.random()<.30 && mode==='live'){
      const i=(Math.random()*pts.length)|0;
      const q=projected[i];
      if(q && q.z>-.2) emitMote(pts[i],q.x,q.y);
    }
  }
  requestAnimationFrame(frame);

  /* ── 9) whole-UI sparkfield: gold/teal/star motes, CSS-animated ──────── */
  if(!REDUCED && !document.getElementById('v197-sparkfield')){
    const field=document.createElement('div');
    field.id='v197-sparkfield';
    field.setAttribute('aria-hidden','true');
    const COLS=['#FFE9A8','#F5D67B','#4EDAA8','#FFFCD7','#9BE4FF','#FFE9A8'];
    for(let i=0;i<22;i++){
      const s=document.createElement('span');
      s.style.setProperty('--x',(Math.random()*100).toFixed(2)+'vw');
      s.style.setProperty('--y',(Math.random()*100).toFixed(2)+'vh');
      s.style.setProperty('--s',(1.6+Math.random()*2.6).toFixed(2)+'px');
      s.style.setProperty('--c',COLS[i%COLS.length]);
      s.style.setProperty('--d',(3.6+Math.random()*5.4).toFixed(2)+'s');
      s.style.setProperty('--dl',(-Math.random()*9).toFixed(2)+'s');
      field.appendChild(s);
    }
    document.body.appendChild(field);
  }

  /* ── 10) recolor legacy amber merge-sparks (V5 gate) on the fly ──────── */
  const SPARK_MAP={
    '#ffd23f':'#F5D67B','#f4a01b':'#4EDAA8','#ff8030':'#FFE9A8',
    '#ff5090':'#FF6C80','#fff3bc':'#FFF6CE','#40e870':'#9BEBB4',
    '#40d8ff':'#9BE4FF','#b060ff':'#D0A8FF','#ff60ff':'#FFA8FF'
  };
  new MutationObserver(muts=>{
    for(const mu of muts){
      for(const n of mu.addedNodes){
        if(n.nodeType===1 && n.classList && n.classList.contains('nur-entry-spark')){
          const cur=(n.style.getPropertyValue('--spark')||'').trim().toLowerCase();
          if(SPARK_MAP[cur]) n.style.setProperty('--spark',SPARK_MAP[cur]);
        }
      }
    }
  }).observe(document.body,{childList:true,subtree:true});

  /* debug handle */
  window.__nurV197={
    version:'V197',
    points:pts.length,
    edges:edges.length,
    get mode(){return mode},
    get quality(){return quality},
    canvas
  };
})();
