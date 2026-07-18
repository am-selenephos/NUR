(() => {
  'use strict';
  const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const host = document.getElementById('front-nur-star');
  if(!host) return;
  host.setAttribute('title','drag to spin the mind - click: it dissolves into stardust and reforms - double-click: neural storm - scroll to zoom');
  host.setAttribute('aria-label','A living brain made of stars. Drag to spin it. Click and it dissolves into tiny star glitter, then flows back together.');

  const canvas = document.createElement('canvas');
  canvas.id = 'nur-brain-canvas';
  host.appendChild(canvas);
  const c = canvas.getContext('2d', { alpha:true });

  /* ---- palette: warm-led with restrained prism accents ------------------ */
  const WARM = [[255,216,122],[255,196,86],[255,236,186],[255,176,64],[255,246,214]];
  const PRISM = [[120,225,255],[190,140,255],[255,140,200],[126,237,160]];
  const rnd=(a,b)=>a+Math.random()*(b-a);
  const pick=a=>a[(Math.random()*a.length)|0];

  /* ---- 3D star-brain point cloud ---------------------------------------
     axes: x = left/right (hemispheres), y = up, z = front(+)/back(-) */
  const MOBILE = innerWidth < 700;
  const N_CORTEX = MOBILE ? 430 : 640;
  const N_CEREB  = MOBILE ? 90  : 130;
  const N_STEM   = MOBILE ? 18  : 26;
  const pts = [];

  function addPoint(x,y,z,group,foldDim){
    const warm = Math.random() < .78;
    pts.push({
      x,y,z, group,
      ox:0, oy:0, oz:0, vx:0, vy:0, vz:0,        // jelly offset + velocity
      r: rnd(.7,2.1) * (group==='stem' ? .8 : 1),
      col: warm ? pick(WARM) : pick(PRISM),
      tw: rnd(0,Math.PI*2), tws: rnd(.010,.032), twa: rnd(.25,.55),
      dim: foldDim||0
    });
  }
  // cortex: golden-spiral sphere -> brain ellipsoid + gyri folds + fissure
  for(let i=0;i<N_CORTEX;i++){
    const t=(i+.5)/N_CORTEX;
    const inc=Math.acos(1-2*t), az=Math.PI*(1+Math.sqrt(5))*i;
    let x=Math.sin(inc)*Math.cos(az), y=Math.cos(inc), z=Math.sin(inc)*Math.sin(az);
    // gyri: two interleaved wrinkle frequencies along the surface
    let fold = .058*Math.sin(az*7 + Math.sin(inc*4)*1.8) + .036*Math.sin(az*13 + inc*9);
    const nearFissure = Math.abs(x) < .12 && y > -.15;
    if(nearFissure) fold = -.05;                       // groove, not ridge
    const f = 1 + fold;
    x*=f; y*=f; z*=f;
    // ellipsoid proportions
    x*=1.00; y*=.83; z*=1.26;
    // longitudinal fissure: push hemispheres apart at the midline
    if(Math.abs(x) < .11 && y > -.12) x = Math.sign(x||rnd(-1,1)) * (.11 + Math.abs(x)*.35);
    // frontal taper + flattened underside + temporal bulge
    if(z > .55) x *= 1 - .16*(z-.55);
    if(y < -.42) y = -.42 + (y+.42)*.45;
    if(y < -.05 && Math.abs(x) > .52 && z > .1) y -= .07;
    addPoint(x,y,z,'cortex', nearFissure ? .45 : 0);
  }
  // cerebellum: small finely-striped ellipsoid, lower back
  for(let i=0;i<N_CEREB;i++){
    const t=(i+.5)/N_CEREB;
    const inc=Math.acos(1-2*t), az=Math.PI*(1+Math.sqrt(5))*i;
    let x=Math.sin(inc)*Math.cos(az), y=Math.cos(inc), z=Math.sin(inc)*Math.sin(az);
    const f = 1 + .045*Math.sin(inc*16);               // horizontal striations
    addPoint(x*.55*f, -.55 + y*.30*f, -.80 + z*.42*f, 'cereb', .1);
  }
  // brainstem: short curved column
  for(let i=0;i<N_STEM;i++){
    const t=i/N_STEM, a=rnd(0,Math.PI*2), rr=rnd(0,.11);
    addPoint(Math.cos(a)*rr, -.44 - t*.42, -.42 + t*.18 + Math.sin(a)*rr, 'stem', .15);
  }

  /* ---- synapse edges (k-nearest within same tissue) --------------------- */
  const edges=[]; const adj=pts.map(()=>[]);
  for(let i=0;i<pts.length;i++){
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
      if(!edges.some(e=>e.key===key)){
        edges.push({key,a:i,b:j});
        adj[i].push(j); adj[j].push(i);
      }
    }
  }

  /* ---- neural pulses (thought signals travelling the synapses) ---------- */
  const pulses=[];
  function firePulse(from){
    const start = from ?? (Math.random()*pts.length)|0;
    const path=[start]; let cur=start;
    for(let h=0;h<3+((Math.random()*4)|0);h++){
      const next=adj[cur][(Math.random()*adj[cur].length)|0];
      if(next==null) break;
      path.push(next); cur=next;
    }
    if(path.length>1) pulses.push({path, t:0, speed:rnd(.028,.05), col:Math.random()<.6?pick(PRISM):pick(WARM)});
  }

  /* ---- glitter motes drifting off the surface --------------------------- */
  const motes=[];
  function emitMote(p, px, py){
    if(motes.length>44) return;
    motes.push({x:px, y:py, vx:rnd(-.22,.22), vy:rnd(-.5,-.14), life:rnd(38,80), max:80, col:p?p.col:pick(WARM), r:rnd(.6,1.6)});
  }

  /* ---- camera / interaction state --------------------------------------- */
  let W=0,H=0,cx=0,cy=0,scale=1,DPR=1;
  let yaw=.85, pitch=-.14, vyaw=REDUCED?0:.0022, vpitch=0;
  let zoom=1, targetZoom=1;
  let dragging=false, dragDist=0, lx=0, ly=0;
  let hoverX=-1e4, hoverY=-1e4;
  let mode='live', modeT=0;      // live | absorb | bloom
  let energy=0;                  // storm brightness boost
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
  // the host lives inside #welcome which starts display:none - the first real
  // measurement only exists once the front page reveals, so watch the box itself
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

  function star4(x,y,r,rot){
    c.beginPath();
    for(let i=0;i<8;i++){
      const rr=i%2===0?r:r*.32, a=rot+i*Math.PI/4;
      const px=x+Math.cos(a)*rr, py=y+Math.sin(a)*rr;
      i===0?c.moveTo(px,py):c.lineTo(px,py);
    }
    c.closePath();
  }

  /* ---- storms / absorb / bloom ------------------------------------------ */
  function storm(power=1){
    energy=Math.min(1.6, energy+power);
    const n=Math.round(10+16*power);
    for(let i=0;i<n;i++) setTimeout(()=>firePulse(), Math.random()*420);
    // jelly shockwave
    for(const p of pts){
      const m=Math.hypot(p.x,p.y,p.z)||1;
      const k=.028*power;
      p.vx+=p.x/m*k*rnd(.4,1); p.vy+=p.y/m*k*rnd(.4,1); p.vz+=p.z/m*k*rnd(.4,1);
    }
  }
  function absorb(){ mode='absorb'; modeT=0; }
  /* the mind dissolves into tiny star glitter, drifts, then flows back together */
  function shatter(){
    if(mode==='shatter' || mode==='reform') return;
    mode='shatter'; modeT=0;
    pulses.length=0;
    energy=Math.min(1.6, energy+1);
    for(const p of pts){
      const m=Math.hypot(p.x,p.y,p.z)||1;
      const s=rnd(.055,.16);
      p.vx += p.x/m*s + rnd(-.045,.045);
      p.vy += p.y/m*s + rnd(-.045,.045) + .015;   // a little lift: glitter rises
      p.vz += p.z/m*s + rnd(-.045,.045);
    }
    for(let i=0;i<28;i++){
      const q=projected[(Math.random()*pts.length)|0];
      if(q) emitMote(null,q.x,q.y);
    }
  }
  window.nurStarBrain={ storm, absorb, shatter, firePulse };

  // map the existing V4/V5 class rituals onto the brain:
  // single click ritual (.is-bursting) = dissolve into stardust and reform;
  // step-inside ritual (.is-entry-absorbing) = collapse then bloom.
  new MutationObserver(()=>{
    if(host.classList.contains('is-entry-absorbing')) absorb();
    else if(host.classList.contains('is-bursting') && mode==='live') shatter();
  }).observe(host,{attributes:true,attributeFilter:['class']});

  /* ---- interaction ------------------------------------------------------- */
  canvas.addEventListener('pointerdown',e=>{
    dragging=true; dragDist=0; lx=e.clientX; ly=e.clientY;
    host.classList.add('is-grabbing');
    try{canvas.setPointerCapture(e.pointerId)}catch{}
    e.stopPropagation();                       // keep the galaxy camera out of it
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
    if(dragDist>7){ e.stopPropagation(); return; }  // a drag is not a click
    // the host's own V4 click handler adds .is-bursting -> observer -> shatter (stardust dissolve)
  });
  canvas.addEventListener('wheel',e=>{
    e.preventDefault();
    targetZoom=Math.max(.72,Math.min(1.5,targetZoom + (e.deltaY<0?.09:-.09)));
  },{passive:false});
  canvas.addEventListener('dblclick',e=>{ e.stopPropagation(); storm(1.4); });

  /* ---- ambient rhythms ---------------------------------------------------- */
  if(!REDUCED){
    setInterval(()=>{ if(mode==='live' && !document.hidden && pulses.length<9) firePulse(); }, 640);
  }

  /* ---- render loop -------------------------------------------------------- */
  let projected = new Array(pts.length);
  function frame(now){
    requestAnimationFrame(frame);
    if(document.hidden) return;
    const welcome=document.getElementById('welcome');
    if(welcome && getComputedStyle(welcome).display==='none') return;
    if(W<10){ resize(); if(W<10) return; }   // first visible frame after reveal

    breath += .012;
    energy *= .965;
    zoom += (targetZoom-zoom)*.08;
    if(!dragging && !REDUCED){
      vyaw += (.0022 - vyaw)*.02;              // settle back to idle spin
      vpitch *= .92;
      yaw += vyaw; pitch = Math.max(-1.1,Math.min(1.1,pitch+vpitch))*.996;
    }

    // mode cycles: absorb -> bloom (step-inside) / shatter -> reform (click)
    let squeeze=1, cohesion=1, springK=.06, dampK=.86;
    if(mode==='absorb'){
      modeT++; squeeze=1-Math.min(.5,modeT*.032);
      if(modeT>24){
        mode='bloom'; modeT=0;
        storm(1.5);
      }
    } else if(mode==='bloom'){
      modeT++; squeeze=.5+Math.min(.5,modeT*.05);
      if(modeT>34) mode='live';
    } else if(mode==='shatter'){
      // stardust phase: spring nearly off, glitter drifts free
      modeT++; springK=.0022; dampK=.986;
      cohesion=Math.max(0,1-modeT*.055);
      if(modeT>80){ mode='reform'; modeT=0; }
    } else if(mode==='reform'){
      // the mind flows back together
      modeT++; springK=.026; dampK=.885;
      cohesion=Math.min(1,modeT*.018);
      if(modeT>95) mode='live';
    }

    // jelly physics: spring back to true anatomy
    for(const p of pts){
      p.vx+=-springK*p.ox; p.vy+=-springK*p.oy; p.vz+=-springK*p.oz;
      p.vx*=dampK; p.vy*=dampK; p.vz*=dampK;
      p.ox+=p.vx; p.oy+=p.vy; p.oz+=p.vz;
    }

    c.clearRect(0,0,W,H);

    // soft core glow behind the mind
    const g=c.createRadialGradient(cx,cy,0,cx,cy,scale*1.5);
    g.addColorStop(0,`rgba(255,196,86,${.075+energy*.06})`);
    g.addColorStop(.45,`rgba(190,140,255,${.028+energy*.03})`);
    g.addColorStop(1,'rgba(0,0,0,0)');
    c.fillStyle=g; c.fillRect(0,0,W,H);

    // project all points (with squeeze + gentle float)
    const bob = REDUCED?0:Math.sin(breath*.7)*.02;
    for(let i=0;i<pts.length;i++){
      const p=pts[i];
      const bx=p.x, by=p.y, bz=p.z;
      p.x*=squeeze; p.y=p.y*squeeze+bob; p.z*=squeeze;
      projected[i]=project(p);
      p.x=bx; p.y=by; p.z=bz;
    }

    // synapse web (depth-faded, warm; dissolves with the mind)
    if(cohesion>.06){
      c.lineWidth=.55;
      for(const e of edges){
        const A=projected[e.a], B=projected[e.b];
        const depth=(A.z+B.z)*.5;
        const al=(.055+Math.max(0,depth)*.075)*(1+energy*.8)*cohesion;
        if(al<.03) continue;
        c.strokeStyle=`rgba(255,214,140,${Math.min(.22,al)})`;
        c.beginPath(); c.moveTo(A.x,A.y); c.lineTo(B.x,B.y); c.stroke();
      }
    }

    // stars, back-to-front
    const order=[...pts.keys()].sort((a,b)=>projected[a].z-projected[b].z);
    for(const i of order){
      const p=pts[i], q=projected[i];
      p.tw+=p.tws;
      const twinkle=1-p.twa+p.twa*(.5+.5*Math.sin(p.tw));
      const flash=Math.random()>.998?1.9:1;
      const lit=.42+.58*Math.max(0,Math.min(1,(q.z+ .9)/1.7));   // front-facing glow
      let a=(.32+.68*lit)*twinkle*flash*(1-p.dim)*(1+energy*.55);
      // hover ripple: nearby stars brighten and get pushed
      const hd=Math.hypot(q.x-hoverX,q.y-hoverY);
      if(hd<58){
        const k=1-hd/58;
        a*=1+.9*k;
        p.vx+=(p.x)*.0016*k; p.vy+=(p.y)*.0016*k; p.vz+=(p.z)*.0016*k;
        if(Math.random()<.05*k) emitMote(p,q.x,q.y);
      }
      a=Math.min(1,a);
      // as stardust: finer grains, quicker sparkle
      const r=Math.max(.55,p.r*q.sc*2.5*zoom*(.62+.38*cohesion));
      if(cohesion<1) p.tw+=p.tws*(1-cohesion)*1.6;
      const [cr,cg,cb]=p.col;
      // halo
      const hg=c.createRadialGradient(q.x,q.y,0,q.x,q.y,r*3.4);
      hg.addColorStop(0,`rgba(${cr},${cg},${cb},${a*.30})`);
      hg.addColorStop(1,'rgba(0,0,0,0)');
      c.fillStyle=hg; c.beginPath(); c.arc(q.x,q.y,r*3.4,0,Math.PI*2); c.fill();
      // crystalline 4-point body
      c.fillStyle=`rgba(255,250,228,${a*.92})`;
      star4(q.x,q.y,r,p.tw*.25); c.fill();
      c.fillStyle=`rgba(${cr},${cg},${cb},${a*.55})`;
      star4(q.x,q.y,r*1.7,p.tw*.25+Math.PI/4); c.fill();
    }

    // travelling neural pulses
    for(let i=pulses.length-1;i>=0;i--){
      const pu=pulses[i];
      pu.t+=pu.speed;
      const seg=Math.floor(pu.t), f=pu.t-seg;
      if(seg>=pu.path.length-1){ pulses.splice(i,1); continue; }
      const A=projected[pu.path[seg]], B=projected[pu.path[seg+1]];
      const x=A.x+(B.x-A.x)*f, y=A.y+(B.y-A.y)*f;
      const [cr,cg,cb]=pu.col;
      // trail
      c.strokeStyle=`rgba(${cr},${cg},${cb},.5)`;
      c.lineWidth=1.1;
      c.beginPath(); c.moveTo(A.x,A.y); c.lineTo(x,y); c.stroke();
      // spark head
      const pg=c.createRadialGradient(x,y,0,x,y,7);
      pg.addColorStop(0,`rgba(255,252,232,.95)`);
      pg.addColorStop(.3,`rgba(${cr},${cg},${cb},.75)`);
      pg.addColorStop(1,'rgba(0,0,0,0)');
      c.fillStyle=pg; c.beginPath(); c.arc(x,y,7,0,Math.PI*2); c.fill();
    }

    // drifting glitter motes
    for(let i=motes.length-1;i>=0;i--){
      const m=motes[i];
      m.x+=m.vx; m.y+=m.vy; m.life--;
      if(m.life<=0){ motes.splice(i,1); continue; }
      const a=(m.life/m.max)*.8;
      const [cr,cg,cb]=m.col;
      c.fillStyle=`rgba(${cr},${cg},${cb},${a})`;
      star4(m.x,m.y,m.r+ .6,m.life*.2); c.fill();
    }

    // ambient sparkle emission from the surface
    if(!REDUCED && Math.random()<.30 && mode==='live'){
      const i=(Math.random()*pts.length)|0;
      const q=projected[i];
      if(q.z>-.2) emitMote(pts[i],q.x,q.y);
    }
  }
  requestAnimationFrame(frame);
})();
