'use strict';
// Placing an added stroke or small kana beside a kana. Every Noto contour is a part that can be
// selected (click; Shift or Ctrl adds), moved, scaled, turned and weighted on its own; each group
// (the added part, the kana) has its own controls on top. Transforms are applied point for point
// as okinawan_merge does; weights come from outlines drawn ahead of time at every grid weight.
const $=id=>document.getElementById(id), storageKey='tune:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,p:structuredClone(START),group:'mark',sel:[],tint:false,dark:null};
for(const k in START)state.p[k]??=structuredClone(START[k]);
state.sel??=[];state.group??='mark';
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state))}catch{}}

// ---- geometry, mirrored from okinawan_merge ----
const pts4=seg=>[[seg[0],seg[1]],[seg[2],seg[3]],[seg[4],seg[5]],[seg[6],seg[7]]];
const snap=d=>{const i=Math.max(0,Math.min(BOLDS.length-1,Math.round(d/2)));return BOLDS[i]};
const partOf=key=>state.p.parts[key]||{};
// a contour at a weight, falling back to the nearest lighter weight that could be drawn
function weighted(part,d){let b=snap(d);while(b>0&&!part.by_bold[String(b)])b-=2;return part.by_bold[String(b)]}
// part_affine: scale and turn about the part's centre, then move
function partAffine(rings,centre,t){const a=(t.rot||0)*Math.PI/180,c=Math.cos(a),s=Math.sin(a),sx=t.sx??1,sy=t.sy??1,[cx,cy]=centre,dx=t.dx||0,dy=t.dy||0;
 return rings.map(r=>r.map(seg=>seg.map(([x,y])=>{x=(x-cx)*sx;y=(y-cy)*sy;return [cx+c*x-s*y+dx,cy+s*x+c*y+dy]})))}
const kanaGroup=([x,y],p)=>{const [ox,oy]=KANA_ORIGIN;return [ox+(x-ox)*p.kana_sx+p.kana_dx,oy+(y-oy)*p.kana_sy+p.kana_dy]};
function kanaRings(p){ // [{key, rings}]
 return KANA_PARTS.map((part,i)=>{const key='k'+i,t=partOf(key);
  const rings=partAffine(weighted(part,p.kana_bold+(t.bold||0)).map(r=>r.map(pts4)),part.centre,t);
  return {key,rings:rings.map(r=>r.map(seg=>seg.map(q=>kanaGroup(q,p))))}})}
function markRings(p){ // [{key, rings}]
 let items,px,py;
 if(STROKE.multi){
  [px,py]=STROKE.pivots[String(snap(p.mark_bold))]||Object.values(STROKE.pivots)[0];
  items=STROKE.parts.map((part,i)=>{const key='m'+i,t=partOf(key);return {key,rings:partAffine(weighted(part,p.mark_bold+(t.bold||0)).map(r=>r.map(pts4)),part.centre,t)}});
 }else{
  // one stroke, widened about its centre line (neck_w at the ramp's low end, head_w from its high end up)
  const {segs,lo,hi,c0,c1}=STROKE;px=c0;py=lo;
  items=[{key:'m0',rings:[segs.map(seg=>pts4(seg).map(([x,y])=>{const u=Math.min(1,Math.max(0,(y-lo)/(hi-lo))),cx=c0+(c1-c0)*u,k=p.neck_w+(p.head_w-p.neck_w)*u;return [cx+(x-cx)*k,y]}))]}];
 }
 const a=p.mark_angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
 const each=f=>items.forEach(it=>{it.rings=it.rings.map(r=>r.map(seg=>seg.map(f)))});
 each(([x,y])=>{x-=px;y-=py;return [px+c*x-s*y,py+s*x+c*y]});
 const all=()=>items.flatMap(it=>it.rings.flat(2));
 const ys=all().map(q=>q[1]),y0=Math.min(...ys),y1=Math.max(...ys);
 // bow (the middle moves, the ends stay) and slant (the top moves, the foot stays)
 each(([x,y])=>{const u=(y-y0)/(y1-y0);return [x+p.mark_bend*4*u*(1-u)+p.mark_slant*u,y]});
 // head (top third) and tail (bottom third) turn on their own, fading in from the middle
 if(p.head_angle||p.tail_angle){
  const flat=all(),h=(y1-y0)/3;
  const centre=y=>{const band=flat.filter(q=>Math.abs(q[1]-y)<=h/2);return [band.length?(Math.min(...band.map(q=>q[0]))+Math.max(...band.map(q=>q[0])))/2:flat.reduce((t,q)=>t+q[0],0)/flat.length,y]};
  const turns=[[p.head_angle*Math.PI/180,centre(y1-h),q=>(q[1]-(y1-h))/h],[p.tail_angle*Math.PI/180,centre(y0+h),q=>((y0+h)-q[1])/h]];
  each(q=>{for(const [t0,cc,weight] of turns){const w=Math.min(1,Math.max(0,weight(q)));if(t0&&w){const dx=q[0]-cc[0],dy=q[1]-cc[1],t=t0*w;q=[cc[0]+Math.cos(t)*dx-Math.sin(t)*dy,cc[1]+Math.sin(t)*dx+Math.cos(t)*dy]}}return q});
 }
 if(LIE)each(([x,y])=>[-y,x]);   // a lying stroke is laid back down
 // size about the foot, stretch upward, move
 const pool=all(),foot=Math.min(...pool.map(q=>q[1])),fx=pool.reduce((t,q)=>t+q[0],0)/pool.length;
 each(([x,y])=>{x=fx+(x-fx)*p.mark_scale;y=foot+(y-foot)*p.mark_scale;return [x+p.mark_x,foot+(y-foot)*p.mark_len+p.mark_dy]});
 return items;
}
const f1=v=>v.toFixed(1);
const pathOf=rings=>rings.map(r=>'M'+f1(r[0][0][0])+' '+f1(r[0][0][1])+r.map(([,b,c2,d])=>`C${f1(b[0])} ${f1(b[1])} ${f1(c2[0])} ${f1(c2[1])} ${f1(d[0])} ${f1(d[1])}`).join('')+'Z').join('');

// ---- controls ----
const r1=v=>v.toFixed(0), r2=v=>v.toFixed(2), r3=v=>v.toFixed(3);
const both={get:p=>(p.neck_w+p.head_w)/2,set:(p,v)=>{const d=v-(p.neck_w+p.head_w)/2;p.neck_w=+(p.neck_w+d).toFixed(3);p.head_w=+(p.head_w+d).toFixed(3)}};
const kanaSize={get:p=>(p.kana_sx+p.kana_sy)/2,set:(p,v)=>{const d=v-(p.kana_sx+p.kana_sy)/2;p.kana_sx=+(p.kana_sx+d).toFixed(3);p.kana_sy=+(p.kana_sy+d).toFixed(3)}};
const grid=key=>({get:p=>BOLDS.indexOf(snap(p[key])),set:(p,v)=>{p[key]=BOLDS[Math.round(v)]},show:p=>String(p[key])});
// [key, label, min, max, step, format, accessor]
const CONTROLS={stroke:[
 ['Position'],['mark_x','Left / right',-400,600,1,r1],['mark_dy','Down / up',-400,500,1,r1],
 ['Shape'],['mark_scale','Size',.2,2,.005,r3],['mark_len','Length',.2,2.5,.005,r3],['mark_angle','Rotate',-60,60,.5,v=>v.toFixed(1)],
 ['mark_bend','Bow',-200,200,1,r1],['mark_slant','Slant',-250,250,1,r1],['head_angle','Head angle',-90,90,.5,v=>v.toFixed(1)],['tail_angle','Tail angle',-90,90,.5,v=>v.toFixed(1)],
 ...(STROKE.multi?[['Weight'],['mark_bold','Weight',0,BOLDS.length-1,1,null,grid('mark_bold')]]
  :[['Thickness'],['width','Whole stroke',.2,3,.01,r2,both],['head_w','Head',.2,3,.01,r2],['neck_w','Foot',.2,3,.01,r2]]),
],kana:[
 ['kana_dx','Left / right',-300,300,1,r1],['kana_dy','Down / up',-300,300,1,r1],
 ['size','Size',.4,1.4,.005,r3,kanaSize],['kana_sx','Width',.4,1.4,.005,r3],['kana_sy','Height',.4,1.4,.005,r3],
 ['kana_bold','Weight',0,BOLDS.length-1,1,null,grid('kana_bold')],
],part:[
 ['dx','Left / right',-300,300,1,r1],['dy','Down / up',-300,300,1,r1],['sx','Width',.3,2,.005,r3],['sy','Height',.3,2,.005,r3],
 ['rot','Rotate',-90,90,.5,v=>v.toFixed(1)],['bold','Weight',-20,30,2,r1],
]};
const PART_DEFAULT={dx:0,dy:0,sx:1,sy:1,rot:0,bold:0};
// a part control shows the first selected part and moves every selected part by the same amount
const partAcc=key=>({get:()=>{const t=partOf(state.sel[0]);return t[key]??PART_DEFAULT[key]},
 set:(p,v)=>{const d=v-(partOf(state.sel[0])[key]??PART_DEFAULT[key]);const parts={...p.parts};
  for(const k of state.sel){const t={...PART_DEFAULT,...parts[k]};t[key]=+(t[key]+d).toFixed(4);parts[k]=t}p.parts=parts}});
const acc=(group,c)=>group==='part'?partAcc(c[0]):c[6]||{get:p=>p[c[0]],set:(p,v)=>{p[c[0]]=+(+v).toFixed(4)}};
function build(){
 for(const group of ['stroke','kana','part'])$(group+'-rows').innerHTML=CONTROLS[group].map(c=>c.length===1?`<span class="sub">${c[0]}</span>`:
  `<label for="r-${group}-${c[0]}" data-reset="${group}:${c[0]}" title="Double-click to reset">${c[1]}</label><button type="button" class="step" data-step="${group}:${c[0]}" data-dir="-1" aria-label="${c[1]}: less">−</button><input id="r-${group}-${c[0]}" type="range" min="${c[2]}" max="${c[3]}" step="${c[4]}"><button type="button" class="step" data-step="${group}:${c[0]}" data-dir="1" aria-label="${c[1]}: more">+</button><input id="n-${group}-${c[0]}" type="number" step="${c[4]}" aria-label="${c[1]}">`).join('');
 for(const group of ['stroke','kana','part'])for(const c of CONTROLS[group]){if(c.length===1)continue;
  const a=acc(group,c),upd=v=>{if(group==='part'&&!state.sel.length)return;a.set(state.p,+v);render()};
  $(`r-${group}-${c[0]}`).oninput=e=>upd(e.target.value);
  $(`n-${group}-${c[0]}`).onchange=e=>upd(c[6]?.show?BOLDS.indexOf(snap(+e.target.value)):e.target.value);
  // − and + step by ten slider steps (one grid step for weights); Shift for one slider step
  // (a part's weight moves one grid step of 2 either way)
  const unit=e=>c[6]?.show?1:group==='part'&&c[0]==='bold'?c[4]:(e.shiftKey?1:10)*c[4];
  for(const b of document.querySelectorAll(`[data-step="${group}:${c[0]}"]`))b.onclick=e=>upd(a.get(state.p)+ +b.dataset.dir*unit(e));
  document.querySelector(`[data-reset="${group}:${c[0]}"]`).ondblclick=()=>{
   if(group==='part'){for(const k of state.sel){const t={...PART_DEFAULT,...state.p.parts[k]};t[c[0]]=PART_DEFAULT[c[0]];state.p.parts={...state.p.parts,[k]:t}}}
   else a.set(state.p,a.get(START));render()}}
}
function glyph(){return `<svg viewBox="0 0 1000 1000" aria-hidden="true"><g class="centre"><g transform="matrix(1 0 0 -1 0 880)"><path d="${[...kanaRings(state.p),...markRings(state.p)].map(it=>pathOf(it.rings)).join('')}"/></g></g></svg>`}
const selected=key=>state.sel.length?state.sel.includes(key):(key[0]==='m'?state.group==='mark':state.group==='kana');
function render(){
 const p=state.p;
 $('letter').innerHTML=[...kanaRings(p).map(it=>({...it,cls:'kana'})),...markRings(p).map(it=>({...it,cls:'mark'}))]
  .map(it=>`<path class="ink ${it.cls}${selected(it.key)?' sel':''}" data-key="${it.key}" d="${pathOf(it.rings)}"/>`).join('');
 for(const group of ['stroke','kana','part'])for(const c of CONTROLS[group]){if(c.length===1)continue;
  const a=acc(group,c),v=group==='part'&&!state.sel.length?(PART_DEFAULT[c[0]]):a.get(p),r=$(`r-${group}-${c[0]}`),n=$(`n-${group}-${c[0]}`);
  if(document.activeElement!==r)r.value=v;if(document.activeElement!==n)n.value=c[6]?.show?c[6].show(p):c[5](v)}
 $('part-panel').classList.toggle('idle',!state.sel.length);
 $('part-title').textContent=state.sel.length?`Selected part${state.sel.length>1?'s':''}: ${state.sel.map(name).join(', ')}`:'Parts — click one on the stage';
 // the em frame follows the letter, centred on it as the font build centres it
 {const b=$('letter').getBBox(),x=b.x+b.width/2-500;$('em').setAttribute('x',x);$('mid').setAttribute('x1',x+500);$('mid').setAttribute('x2',x+500)}
 $('lines').innerHTML=LINES.map(l=>`<p>${l.replaceAll(LETTER,glyph())}</p>`).join('');
 for(const svg of document.querySelectorAll('#lines svg')){const g=svg.querySelector('.centre'),b=g.getBBox();g.setAttribute('transform',`translate(${500-(b.x+b.width/2)} 0)`)}
 for(const t of ['mark','kana'])$('t-'+t).setAttribute('aria-pressed',!state.sel.length&&state.group===t);
 document.body.classList.toggle('tint',state.tint);$('tint').checked=state.tint;
 persist();
}
const name=key=>(key[0]==='k'?KANA:STROKE.multi?'small kana':'stroke')+' '+(+key.slice(1)+1);
// ---- moving the selection: parts, or else the selected group ----
function move(dx,dy){const p=state.p;
 if(state.sel.length){const parts={...p.parts};for(const k of state.sel){const t={...PART_DEFAULT,...parts[k]};t.dx=+(t.dx+dx).toFixed(2);t.dy=+(t.dy+dy).toFixed(2);parts[k]=t}p.parts=parts}
 else if(state.group==='kana'){p.kana_dx=+(p.kana_dx+dx).toFixed(2);p.kana_dy=+(p.kana_dy+dy).toFixed(2)}
 else{p.mark_x=+(p.mark_x+dx).toFixed(2);p.mark_dy=+(p.mark_dy+dy).toFixed(2)}}
const nudge=(key,d)=>{state.p[key]=+(state.p[key]+d).toFixed(4)};
const KEYS={
 ArrowUp:f=>move(0,f?2:10),ArrowDown:f=>move(0,f?-2:-10),ArrowLeft:f=>move(f?-2:-10,0),ArrowRight:f=>move(f?2:10,0),
 Escape:()=>{state.sel=[]},t:()=>{state.sel=[];state.group=state.group==='kana'?'mark':'kana'},h:()=>{state.tint=!state.tint},
 '-':f=>nudge('mark_scale',f?-.004:-.02),'+':f=>nudge('mark_scale',f?.004:.02),'=':f=>nudge('mark_scale',f?.004:.02),
 '[':f=>nudge('mark_len',f?-.004:-.02),']':f=>nudge('mark_len',f?.004:.02),
 q:f=>nudge('mark_angle',f?.4:2),e:f=>nudge('mark_angle',f?-.4:-2),z:f=>nudge('mark_bend',f?-2:-10),c:f=>nudge('mark_bend',f?2:10),
 a:f=>nudge('mark_slant',f?-2:-10),d:f=>nudge('mark_slant',f?2:10),w:f=>nudge('head_angle',f?1:5),r:f=>nudge('head_angle',f?-1:-5),
 x:f=>nudge('tail_angle',f?1:5),v:f=>nudge('tail_angle',f?-1:-5),
};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'&&!['range','checkbox'].includes(e.target.type)||e.ctrlKey&&e.key!=='Control'&&!e.key.startsWith('Arrow')||e.metaKey||e.altKey)return;
 const fn=KEYS[e.key]||KEYS[e.key.toLowerCase()];if(!fn)return;
 if(e.target.type==='range'&&e.key.startsWith('Arrow'))return;   // a focused slider keeps its own arrows
 e.preventDefault();fn(e.shiftKey);render()});
for(const t of ['mark','kana'])$('t-'+t).onclick=()=>{state.sel=[];state.group=t;render()};
// on the stage: click a part to select it, Shift or Ctrl-click to add or remove one, double-click
// for its whole group, click empty space to clear; drag to move the selection
{let drag=null;const big=$('big');
 big.addEventListener('pointerdown',e=>{const el=e.target.closest('[data-key]');
  if(!el){state.sel=[];render();return}
  const key=el.dataset.key;
  if(e.shiftKey||e.ctrlKey||e.metaKey)state.sel=state.sel.includes(key)?state.sel.filter(k=>k!==key):[...state.sel,key];
  else if(!state.sel.includes(key))state.sel=STROKE.multi||key[0]==='k'?[key]:[];
  if(!state.sel.length)state.group=key[0]==='k'?'kana':'mark';
  drag={x:e.clientX,y:e.clientY,k:big.getScreenCTM().a};big.setPointerCapture(e.pointerId);e.preventDefault();render()});
 big.addEventListener('dblclick',e=>{const el=e.target.closest('[data-key]');if(!el)return;state.sel=[];state.group=el.dataset.key[0]==='k'?'kana':'mark';render()});
 big.addEventListener('pointermove',e=>{if(!drag)return;const dx=(e.clientX-drag.x)/drag.k,dy=-(e.clientY-drag.y)/drag.k;
  if(Math.abs(dx)+Math.abs(dy)<.5)return;drag.x=e.clientX;drag.y=e.clientY;move(dx,dy);render()});
 for(const ev of ['pointerup','pointercancel'])big.addEventListener(ev,()=>{drag=null});}
$('tint').onchange=e=>{state.tint=e.target.checked;render()};
const applyDark=()=>{const dark=state.dark??matchMedia('(prefers-color-scheme: dark)').matches;document.body.classList.toggle('dark',dark);document.body.classList.toggle('light',!dark);$('dark').checked=dark};
$('dark').onchange=e=>{state.dark=e.target.checked;applyDark();persist()};
$('reset').onclick=()=>{state.p=structuredClone(START);state.sel=[];render()};
$('copy').onclick=async()=>{const text=JSON.stringify({arena:EXPERIMENT,protocol:'tune-v1',params:state.p,notes:$('notes').value});
 try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied — paste it into the conversation'}catch{prompt('Copy this result:',text)}};
if(STROKE.multi){document.querySelector('#stroke-panel h2').textContent='Small kana';$('t-mark').textContent='Small kana'}
$('t-kana').textContent=KANA;
build();applyDark();render();
