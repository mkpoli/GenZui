'use strict';
// Direct placement of the glottal mark beside a kana that stays put. The mark's outline is
// drawn once; placing it is a translation, and its size and length are scalings about its
// foot, the same transforms the font build applies.
const $=id=>document.getElementById(id), storageKey='tune:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,p:{...START}};
for(const k in START)state.p[k]??=START[k];
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('saved').textContent='Saved in this browser'}catch{$('saved').textContent='Browser storage unavailable — copy the result before closing'}}
const kanaOf=p=>KANAS[`${p.kana_sx.toFixed(2)},${p.kana_bold}`];
// The mark's outline, shaped and placed point for point as okinawan_merge.shaped and .sized do:
// turn about the pivot, bow and slant, lay a lying stroke down, then size about the foot, stretch, and move.
function markPath(p){
 const {segs,pivot}=MARKS[`${p.neck_w.toFixed(2)},${p.head_w.toFixed(2)}`];
 const a=p.mark_angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a),[px,py]=pivot;
 let pts=segs.map(seg=>{const q=[];for(let i=0;i<8;i+=2){const x=seg[i]-px,y=seg[i+1]-py;q.push([px+c*x-s*y,py+s*x+c*y])}return q});
 const ys=pts.flat().map(q=>q[1]),y0=Math.min(...ys),y1=Math.max(...ys);
 pts=pts.map(seg=>seg.map(([x,y])=>{const u=(y-y0)/(y1-y0);return [x+p.mark_bend*4*u*(1-u)+p.mark_slant*u,y]}));
 if(LIE)pts=pts.map(seg=>seg.map(([x,y])=>[-y,x]));   // a lying stroke is laid back down
 const all=pts.flat(),foot=Math.min(...all.map(q=>q[1])),fx=all.reduce((t,q)=>t+q[0],0)/all.length;
 pts=pts.map(seg=>seg.map(([x,y])=>{x=fx+(x-fx)*p.mark_scale;y=foot+(y-foot)*p.mark_scale;return [x+p.mark_x,foot+(y-foot)*p.mark_len+p.mark_dy]}));
 const f=v=>v.toFixed(1);
 return 'M'+f(pts[0][0][0])+' '+f(pts[0][0][1])+pts.map(([,b,c2,d])=>`C${f(b[0])} ${f(b[1])} ${f(c2[0])} ${f(c2[1])} ${f(d[0])} ${f(d[1])}`).join('')+'Z';
}
function glyph(){return `<svg viewBox="0 0 1000 1000" aria-hidden="true"><g class="centre"><g transform="matrix(1 0 0 -1 0 880)"><path class="ink" d="${kanaOf(state.p)}"/><path class="ink" d="${markPath(state.p)}"/></g></g></svg>`}
function render(){
 const p=state.p;
 $('mark').setAttribute('d',markPath(p));$('kana').setAttribute('d',kanaOf(p));
 $('values').innerHTML=`<dt>right</dt><dd>${p.mark_x.toFixed(0)}</dd><dt>up</dt><dd>${p.mark_dy.toFixed(0)}</dd><dt>size</dt><dd>${p.mark_scale.toFixed(3)}</dd><dt>length</dt><dd>${p.mark_len.toFixed(3)}</dd><dt>angle</dt><dd>${p.mark_angle.toFixed(1)}°</dd><dt>bend</dt><dd>${p.mark_bend.toFixed(0)}</dd><dt>slant</dt><dd>${p.mark_slant.toFixed(0)}</dd><dt>foot width</dt><dd>${p.neck_w.toFixed(2)}</dd><dt>head width</dt><dd>${p.head_w.toFixed(2)}</dd><dt>kana ${EVEN?'size':'width'}</dt><dd>${p.kana_sx.toFixed(2)}</dd><dt>kana weight</dt><dd>${p.kana_bold}</dd>`;
 $('lines').innerHTML=LINES.map(l=>`<p>${l.replaceAll(LETTER,glyph())}</p>`).join('');
 // centre each small copy in its em, as the font build does
 for(const svg of document.querySelectorAll('#lines svg')){const g=svg.querySelector('.centre'),b=g.getBBox();g.setAttribute('transform',`translate(${500-(b.x+b.width/2)} 0)`)}
 persist();
}
const ACTS={up:(p,s)=>p.mark_dy+=s,down:(p,s)=>p.mark_dy-=s,left:(p,s)=>p.mark_x-=s,right:(p,s)=>p.mark_x+=s,
 bigger:(p,s)=>p.mark_scale=+(p.mark_scale+s/500).toFixed(3),smaller:(p,s)=>p.mark_scale=+(p.mark_scale-s/500).toFixed(3),
 longer:(p,s)=>p.mark_len=+(p.mark_len+s/500).toFixed(3),shorter:(p,s)=>p.mark_len=+(p.mark_len-s/500).toFixed(3),
 thinner:p=>{widen(p,'neck_w',-1);widen(p,'head_w',-1)},thicker:p=>{widen(p,'neck_w',1);widen(p,'head_w',1)},
 head_thinner:p=>widen(p,'head_w',-1),head_thicker:p=>widen(p,'head_w',1),neck_thinner:p=>widen(p,'neck_w',-1),neck_thicker:p=>widen(p,'neck_w',1),
 kana_lighter:p=>{p.kana_bold=BOLDS[Math.max(0,BOLDS.indexOf(p.kana_bold)-1)]},kana_heavier:p=>{p.kana_bold=BOLDS[Math.min(BOLDS.length-1,BOLDS.indexOf(p.kana_bold)+1)]},
 ccw:(p,s)=>p.mark_angle=+(p.mark_angle+s/5).toFixed(1),cw:(p,s)=>p.mark_angle=+(p.mark_angle-s/5).toFixed(1),
 bend_left:(p,s)=>p.mark_bend-=s,bend_right:(p,s)=>p.mark_bend+=s,slant_left:(p,s)=>p.mark_slant-=s,slant_right:(p,s)=>p.mark_slant+=s,
 kana_narrower:p=>step(p,'kana_sx',NARROWS,-1),kana_wider:p=>step(p,'kana_sx',NARROWS,1),
 reset:p=>Object.assign(p,START)};
function step(p,key,grid,dir){const i=grid.findIndex(v=>Math.abs(v-p[key])<1e-6);p[key]=grid[Math.max(0,Math.min(grid.length-1,i+dir))]}
// widths and weights come in the steps drawn for this page
function widen(p,key,dir){const i=WIDTHS.findIndex(w=>Math.abs(w-p[key])<1e-6);p[key]=WIDTHS[Math.max(0,Math.min(WIDTHS.length-1,i+dir))]}
function act(name,fine){ACTS[name](state.p,fine?2:10);render()}
document.querySelectorAll('[data-act]').forEach(b=>b.onclick=e=>act(b.dataset.act,e.shiftKey));
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'||e.ctrlKey||e.metaKey||e.altKey)return;
 const name={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right','+':'bigger','=':'bigger','-':'smaller',']':'longer','[':'shorter',',':'thinner','.':'thicker',';':'kana_lighter',"'":'kana_heavier','<':'kana_narrower','>':'kana_wider',q:'ccw',e:'cw',Q:'ccw',E:'cw',z:'bend_left',c:'bend_right',Z:'bend_left',C:'bend_right',a:'slant_left',d:'slant_right',A:'slant_left',D:'slant_right'}[e.key];
 if(name){e.preventDefault();act(name,e.shiftKey)}});
$('copy').onclick=async()=>{const text=JSON.stringify({arena:EXPERIMENT,protocol:'tune-v1',params:state.p,notes:$('notes').value});
 try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
for(const [act,word] of [['kana_lighter','lighter'],['kana_heavier','heavier'],['kana_narrower',EVEN?'smaller':'narrower'],['kana_wider',EVEN?'larger':'wider']])document.querySelector(`[data-act=${act}]`).textContent=`${KANA} ${word}`;
render();
