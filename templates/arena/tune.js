'use strict';
// Direct placement of an added stroke beside a kana. The page shapes and places the stroke
// point for point as okinawan_merge does, and scales and moves the kana the same way; only
// the kana's weight comes from outlines drawn ahead of time (KANAS, one per weight).
const $=id=>document.getElementById(id), storageKey='tune:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,p:{...START},target:'stroke',ring:null,tint:false,dark:null};
for(const k in START)state.p[k]??=START[k];
state.p.ring_offsets??={};
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state))}catch{}}

// ---- geometry, mirrored from okinawan_merge ----
function markPath(p){
 const a=p.mark_angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
 let rings,px,py;
 if(STROKE.multi){
  // a small kana, drawn at this weight ahead of time, turned about its middle
  const m=STROKE.by_bold[String(p.mark_bold)];[px,py]=m.pivot;
  // a stroke moved within the small kana keeps its offset (by Noto contour index)
  rings=m.rings.map((r,k)=>{const [ox,oy]=p.ring_offsets[m.groups[k]]||[0,0];
   return r.map(seg=>{const q=[];for(let i=0;i<8;i+=2)q.push([seg[i]+ox,seg[i+1]+oy]);return q})});
 }else{
  // one stroke, widened about its centre line (neck_w at the ramp's low end, head_w from its high end up)
  const {segs,lo,hi,c0,c1}=STROKE;px=c0;py=lo;
  rings=[segs.map(seg=>{const q=[];for(let i=0;i<8;i+=2){let x=seg[i],y=seg[i+1];
   const u=Math.min(1,Math.max(0,(y-lo)/(hi-lo))),cx=c0+(c1-c0)*u,k=p.neck_w+(p.head_w-p.neck_w)*u;q.push([cx+(x-cx)*k,y])}return q})];
 }
 const turn=([x,y])=>{x-=px;y-=py;return [px+c*x-s*y,py+s*x+c*y]};
 let pts=rings.map(r=>r.map(seg=>seg.map(turn)));
 const ys=pts.flat(2).map(q=>q[1]),y0=Math.min(...ys),y1=Math.max(...ys);
 // bow (the middle moves, the ends stay) and slant (the top moves, the foot stays)
 pts=pts.map(r=>r.map(seg=>seg.map(([x,y])=>{const u=(y-y0)/(y1-y0);return [x+p.mark_bend*4*u*(1-u)+p.mark_slant*u,y]})));
 // head (top third) and tail (bottom third) turn on their own, fading in from the middle
 if(p.head_angle||p.tail_angle){
  const flat=pts.flat(2),h=(y1-y0)/3;
  const centre=y=>{const band=flat.filter(q=>Math.abs(q[1]-y)<=h/2);return [band.length?(Math.min(...band.map(q=>q[0]))+Math.max(...band.map(q=>q[0])))/2:flat.reduce((t,q)=>t+q[0],0)/flat.length,y]};
  const turns=[[p.head_angle*Math.PI/180,centre(y1-h),q=>(q[1]-(y1-h))/h],[p.tail_angle*Math.PI/180,centre(y0+h),q=>((y0+h)-q[1])/h]];
  pts=pts.map(r=>r.map(seg=>seg.map(q=>{for(const [t0,cc,weight] of turns){const w=Math.min(1,Math.max(0,weight(q)));if(t0&&w){const dx=q[0]-cc[0],dy=q[1]-cc[1],t=t0*w;q=[cc[0]+Math.cos(t)*dx-Math.sin(t)*dy,cc[1]+Math.sin(t)*dx+Math.cos(t)*dy]}}return q})));
 }
 if(LIE)pts=pts.map(r=>r.map(seg=>seg.map(([x,y])=>[-y,x])));   // a lying stroke is laid back down
 // size about the foot, stretch upward, move
 const all=pts.flat(2),foot=Math.min(...all.map(q=>q[1])),fx=all.reduce((t,q)=>t+q[0],0)/all.length;
 pts=pts.map(r=>r.map(seg=>seg.map(([x,y])=>{x=fx+(x-fx)*p.mark_scale;y=foot+(y-foot)*p.mark_scale;return [x+p.mark_x,foot+(y-foot)*p.mark_len+p.mark_dy]})));
 const f=v=>v.toFixed(1);
 return pts.map(r=>'M'+f(r[0][0][0])+' '+f(r[0][0][1])+r.map(([,b,c2,d])=>`C${f(b[0])} ${f(b[1])} ${f(c2[0])} ${f(c2[1])} ${f(d[0])} ${f(d[1])}`).join('')+'Z');
}
const kanaPath=p=>KANAS[String(p.kana_bold)];
const kanaTransform=p=>{const [ox,oy]=KANA_ORIGIN;return `translate(${ox*(1-p.kana_sx)+p.kana_dx} ${oy*(1-p.kana_sy)+p.kana_dy}) scale(${p.kana_sx} ${p.kana_sy})`};

// ---- controls ----
const r1=v=>v.toFixed(0), r2=v=>v.toFixed(2), r3=v=>v.toFixed(3);
const both={get:p=>(p.neck_w+p.head_w)/2,set:(p,v)=>{const d=v-(p.neck_w+p.head_w)/2;p.neck_w=+(p.neck_w+d).toFixed(3);p.head_w=+(p.head_w+d).toFixed(3)}};
const kanaSize={get:p=>(p.kana_sx+p.kana_sy)/2,set:(p,v)=>{const d=v-(p.kana_sx+p.kana_sy)/2;p.kana_sx=+(p.kana_sx+d).toFixed(3);p.kana_sy=+(p.kana_sy+d).toFixed(3)}};
const CONTROLS={stroke:[
 ['Position'],
 ['mark_x','Left / right',-400,400,1,r1],['mark_dy','Down / up',-400,500,1,r1],
 ['Shape'],
 ['mark_scale','Size',.2,2,.005,r3],['mark_len','Length',.2,2.5,.005,r3],['mark_angle','Rotate',-60,60,.5,v=>v.toFixed(1)],
 ['mark_bend','Bow',-200,200,1,r1],['mark_slant','Slant',-250,250,1,r1],['head_angle','Head angle',-90,90,.5,v=>v.toFixed(1)],['tail_angle','Tail angle',-90,90,.5,v=>v.toFixed(1)],
 ...(STROKE.multi?[['Weight'],['mark_bold','Weight',0,MARK_BOLDS.length-1,1,v=>String(v),null,'mark']]
  :[['Thickness'],['width','Whole stroke',.2,3,.01,r2,both],['head_w','Head',.2,3,.01,r2],['neck_w','Foot',.2,3,.01,r2]]),
],kana:[
 ['kana_dx','Left / right',-300,300,1,r1],['kana_dy','Down / up',-300,300,1,r1],
 ['size','Size',.4,1.4,.005,r3,kanaSize],['kana_sx','Width',.4,1.4,.005,r3],['kana_sy','Height',.4,1.4,.005,r3],
 ['kana_bold','Weight',0,BOLDS.length-1,1,v=>String(v),null,'kana'],
]};
// weights move along the grid of drawn outlines, skipping any that could not be drawn
const GRID={kana:[BOLDS,v=>KANAS[String(v)]],mark:[MARK_BOLDS,v=>!STROKE.multi||STROKE.by_bold[String(v)]]};
function getv(c,p){return c[6]?c[6].get(p):c[7]?GRID[c[7]][0].indexOf(p[c[0]]):p[c[0]]}
function setv(c,p,v){if(c[6])c[6].set(p,v);else if(c[7]){const [grid,ok]=GRID[c[7]];let i=Math.round(v);while(i>0&&!ok(grid[i]))i--;p[c[0]]=grid[i]}else p[c[0]]=+(+v).toFixed(4)}
function build(){
 for(const group of ['stroke','kana'])$(group+'-rows').innerHTML=CONTROLS[group].map(c=>c.length===1?`<span class="sub">${c[0]}</span>`:
  `<label for="r-${c[0]}" data-reset="${c[0]}" title="Double-click to reset">${c[1]}</label><button type="button" class="step" data-step="${c[0]}" data-dir="-1" aria-label="${c[1]}: less">−</button><input id="r-${c[0]}" type="range" min="${c[2]}" max="${c[3]}" step="${c[4]}"><button type="button" class="step" data-step="${c[0]}" data-dir="1" aria-label="${c[1]}: more">+</button><input id="n-${c[0]}" type="number" step="${c[4]}" aria-label="${c[1]}">`).join('');
 for(const group of ['stroke','kana'])for(const c of CONTROLS[group]){if(c.length===1)continue;
  const upd=v=>{setv(c,state.p,v);render()};
  $('r-'+c[0]).oninput=e=>upd(e.target.value);$('n-'+c[0]).onchange=e=>upd(c[7]?GRID[c[7]][0].indexOf(+e.target.value):e.target.value);
  // − and + step by ten slider steps (one grid step for weights); Shift for one slider step
  for(const b of document.querySelectorAll(`[data-step="${c[0]}"]`))b.onclick=e=>{const dir=+b.dataset.dir;
   upd(getv(c,state.p)+dir*(c[7]?1:(e.shiftKey?1:10)*c[4]))};
  document.querySelector(`[data-reset="${c[0]}"]`).ondblclick=()=>{if(c[6]){c[6].set(state.p,c[6].get(START))}else state.p[c[0]]=START[c[0]];render()}}
}
function glyph(){return `<svg viewBox="0 0 1000 1000" aria-hidden="true"><g class="centre"><g transform="matrix(1 0 0 -1 0 880)"><path d="${kanaPath(state.p)}" transform="${kanaTransform(state.p)}"/><path d="${markPath(state.p).join('')}"/></g></g></svg>`}
function render(){
 const p=state.p;
 const groups=STROKE.multi?STROKE.by_bold[String(p.mark_bold)].groups:[null];
 $('mark').innerHTML=markPath(p).map((d,k)=>`<path class="ink mark${state.target==='stroke'&&(state.ring===null||state.ring===groups[k])?' sel':''}" data-part="stroke" data-ring="${groups[k]??''}" d="${d}"/>`).join('');
 $('kana').classList.toggle('sel',state.target==='kana');
 $('selected').textContent=state.target==='kana'?`Selected: ${KANA}`:state.ring!==null?`Selected: stroke ${state.ring+1} of the small kana`:`Selected: ${STROKE.multi?'small kana':'stroke'}`;
 $('kana').setAttribute('d',kanaPath(p));$('kana').setAttribute('transform',kanaTransform(p));
 for(const group of ['stroke','kana'])for(const c of CONTROLS[group]){if(c.length===1)continue;const v=getv(c,p);
  const r=$('r-'+c[0]),n=$('n-'+c[0]);if(document.activeElement!==r)r.value=v;if(document.activeElement!==n)n.value=c[7]?p[c[0]]:c[5](v)}
 // the em frame follows the letter, centred on it as the font build centres it
 {const b=$('letter').getBBox(),x=b.x+b.width/2-500;$('em').setAttribute('x',x);$('mid').setAttribute('x1',x+500);$('mid').setAttribute('x2',x+500)}
 $('lines').innerHTML=LINES.map(l=>`<p>${l.replaceAll(LETTER,glyph())}</p>`).join('');
 for(const svg of document.querySelectorAll('#lines svg')){const g=svg.querySelector('.centre'),b=g.getBBox();g.setAttribute('transform',`translate(${500-(b.x+b.width/2)} 0)`)}
 for(const t of ['stroke','kana'])$('t-'+t).setAttribute('aria-pressed',state.target===t);
 document.body.classList.toggle('tint',state.tint);$('tint').checked=state.tint;
 persist();
}
// ---- keys: arrows move the selected part; letters shape the stroke ----
const nudge=(key,d)=>{state.p[key]=+(state.p[key]+d).toFixed(4)};
// move whatever is selected: the kana, the added part, or one stroke of a small kana
function move(dx,dy){const p=state.p;
 if(state.target==='kana'){p.kana_dx=+(p.kana_dx+dx).toFixed(2);p.kana_dy=+(p.kana_dy+dy).toFixed(2)}
 else if(state.ring!==null){const o=p.ring_offsets[state.ring]||[0,0];p.ring_offsets={...p.ring_offsets,[state.ring]:[+(o[0]+dx).toFixed(2),+(o[1]+dy).toFixed(2)]}}
 else{p.mark_x=+(p.mark_x+dx).toFixed(2);p.mark_dy=+(p.mark_dy+dy).toFixed(2)}}
const KEYS={
 ArrowUp:f=>move(0,f?2:10),ArrowDown:f=>move(0,f?-2:-10),ArrowLeft:f=>move(f?-2:-10,0),ArrowRight:f=>move(f?2:10,0),
 Escape:()=>{state.ring=null},
 '-':f=>nudge('mark_scale',f?-.004:-.02),'+':f=>nudge('mark_scale',f?.004:.02),'=':f=>nudge('mark_scale',f?.004:.02),
 '[':f=>nudge('mark_len',f?-.004:-.02),']':f=>nudge('mark_len',f?.004:.02),
 q:f=>nudge('mark_angle',f?.4:2),e:f=>nudge('mark_angle',f?-.4:-2),z:f=>nudge('mark_bend',f?-2:-10),c:f=>nudge('mark_bend',f?2:10),
 a:f=>nudge('mark_slant',f?-2:-10),d:f=>nudge('mark_slant',f?2:10),w:f=>nudge('head_angle',f?1:5),r:f=>nudge('head_angle',f?-1:-5),
 x:f=>nudge('tail_angle',f?1:5),v:f=>nudge('tail_angle',f?-1:-5),
 ',':f=>both.set(state.p,both.get(state.p)-(f?.01:.05)),'.':f=>both.set(state.p,both.get(state.p)+(f?.01:.05)),
 t:()=>{state.target=state.target==='kana'?'stroke':'kana';state.ring=null},h:()=>{state.tint=!state.tint},
};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'&&e.target.type!=='range'&&e.target.type!=='checkbox'||e.ctrlKey||e.metaKey||e.altKey)return;
 const fn=KEYS[e.key]||KEYS[e.key.toLowerCase()];if(!fn)return;
 if(e.target.type==='range'&&e.key.startsWith('Arrow'))return;   // a focused slider keeps its own arrows
 e.preventDefault();fn(e.shiftKey);render()});
for(const t of ['stroke','kana'])$('t-'+t).onclick=()=>{state.target=t;state.ring=null;render()};
// on the stage: click a part to select it (Shift-click one stroke of a small kana), drag to move it
{let drag=null;const big=$('big');
 big.addEventListener('pointerdown',e=>{const el=e.target.closest('[data-part],#kana');if(!el)return;
  if(el.id==='kana'){state.target='kana';state.ring=null}
  else{state.target='stroke';state.ring=e.shiftKey&&el.dataset.ring!==''?+el.dataset.ring:(e.shiftKey?null:state.target==='stroke'&&state.ring!==null&&+el.dataset.ring===state.ring?state.ring:null)}
  drag={x:e.clientX,y:e.clientY,k:big.getScreenCTM().a};big.setPointerCapture(e.pointerId);e.preventDefault();render()});
 big.addEventListener('pointermove',e=>{if(!drag)return;const dx=(e.clientX-drag.x)/drag.k,dy=-(e.clientY-drag.y)/drag.k;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;drag.x=e.clientX;drag.y=e.clientY;move(dx,dy);render()});
 for(const ev of ['pointerup','pointercancel'])big.addEventListener(ev,()=>{drag=null});}
$('tint').onchange=e=>{state.tint=e.target.checked;render()};
const applyDark=()=>{const dark=state.dark??matchMedia('(prefers-color-scheme: dark)').matches;document.body.classList.toggle('dark',dark);document.body.classList.toggle('light',!dark);$('dark').checked=dark};
$('dark').onchange=e=>{state.dark=e.target.checked;applyDark();persist()};
$('reset').onclick=()=>{state.p={...START,ring_offsets:{...START.ring_offsets}};state.ring=null;render()};
$('copy').onclick=async()=>{const text=JSON.stringify({arena:EXPERIMENT,protocol:'tune-v1',params:state.p,notes:$('notes').value});
 try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied — paste it into the conversation'}catch{prompt('Copy this result:',text)}};
if(STROKE.multi){document.querySelector('#stroke-panel h2').textContent='Small kana';$('t-stroke').textContent='Small kana'}
build();applyDark();render();
