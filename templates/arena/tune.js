'use strict';
// Direct placement of the glottal mark beside a kana that stays put. The mark's outline is
// drawn once; placing it is a translation, and its size and length are scalings about its
// foot, the same transforms the font build applies.
const $=id=>document.getElementById(id), storageKey='tune:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,p:{...START}};
for(const k in START)state.p[k]??=START[k];
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('saved').textContent='Saved in this browser'}catch{$('saved').textContent='Browser storage unavailable — copy the result before closing'}}
const kanaOf=p=>KANAS[String(p.kana_bold)];
// the kana is scaled about its origin, as okinawan_merge.beside_pieces does
const kanaTransform=p=>{const [ox,oy]=KANA_ORIGIN;return `translate(${ox*(1-p.kana_sx)} ${oy*(1-p.kana_sy)}) scale(${p.kana_sx} ${p.kana_sy})`};
// The mark's outline, widened, shaped and placed point for point as okinawan_merge does:
// turn about the pivot, bow and slant, lay a lying stroke down, then size about the foot, stretch, and move.
function markPath(p){
 // widen about the centre line: neck_w at the ramp's low end, head_w from its high end up
 const {segs,lo,hi,c0,c1}=STROKE,px=c0,py=lo;
 const a=p.mark_angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);
 let pts=segs.map(seg=>{const q=[];for(let i=0;i<8;i+=2){let x=seg[i],y=seg[i+1];
  const u=Math.min(1,Math.max(0,(y-lo)/(hi-lo))),cx=c0+(c1-c0)*u,k=p.neck_w+(p.head_w-p.neck_w)*u;x=cx+(x-cx)*k;
  x-=px;y-=py;q.push([px+c*x-s*y,py+s*x+c*y])}return q});
 const ys=pts.flat().map(q=>q[1]),y0=Math.min(...ys),y1=Math.max(...ys);
 pts=pts.map(seg=>seg.map(([x,y])=>{const u=(y-y0)/(y1-y0);return [x+p.mark_bend*4*u*(1-u)+p.mark_slant*u,y]}));
 // the head (top third) and tail (bottom third) turn on their own, fading in from the middle
 if(p.head_angle||p.tail_angle){
  const flat=pts.flat(),h=(y1-y0)/3;
  const centre=y=>{const band=flat.filter(q=>Math.abs(q[1]-y)<=h/2);return [band.length?(Math.min(...band.map(q=>q[0]))+Math.max(...band.map(q=>q[0])))/2:flat.reduce((t,q)=>t+q[0],0)/flat.length,y]};
  const turns=[[p.head_angle*Math.PI/180,centre(y1-h),q=>(q[1]-(y1-h))/h],[p.tail_angle*Math.PI/180,centre(y0+h),q=>((y0+h)-q[1])/h]];
  pts=pts.map(seg=>seg.map(q=>{for(const [a,c,weight] of turns){const w=Math.min(1,Math.max(0,weight(q)));if(a&&w){const dx=q[0]-c[0],dy=q[1]-c[1],t=a*w;q=[c[0]+Math.cos(t)*dx-Math.sin(t)*dy,c[1]+Math.sin(t)*dx+Math.cos(t)*dy]}}return q}));
 }
 if(LIE)pts=pts.map(seg=>seg.map(([x,y])=>[-y,x]));   // a lying stroke is laid back down
 const all=pts.flat(),foot=Math.min(...all.map(q=>q[1])),fx=all.reduce((t,q)=>t+q[0],0)/all.length;
 pts=pts.map(seg=>seg.map(([x,y])=>{x=fx+(x-fx)*p.mark_scale;y=foot+(y-foot)*p.mark_scale;return [x+p.mark_x,foot+(y-foot)*p.mark_len+p.mark_dy]}));
 const f=v=>v.toFixed(1);
 return 'M'+f(pts[0][0][0])+' '+f(pts[0][0][1])+pts.map(([,b,c2,d])=>`C${f(b[0])} ${f(b[1])} ${f(c2[0])} ${f(c2[1])} ${f(d[0])} ${f(d[1])}`).join('')+'Z';
}
function glyph(){return `<svg viewBox="0 0 1000 1000" aria-hidden="true"><g class="centre"><g transform="matrix(1 0 0 -1 0 880)"><path class="ink" d="${kanaOf(state.p)}" transform="${kanaTransform(state.p)}"/><path class="ink" d="${markPath(state.p)}"/></g></g></svg>`}
function render(){
 const p=state.p;
 $('mark').setAttribute('d',markPath(p));$('kana').setAttribute('d',kanaOf(p));$('kana').setAttribute('transform',kanaTransform(p));
 for(const [key,,,fmt] of STEPPERS)if(key)$('v-'+key).value=fmt(p);
 $('lines').innerHTML=LINES.map(l=>`<p>${l.replaceAll(LETTER,glyph())}</p>`).join('');
 // the em frame follows the letter, centred on it as the font build centres it
 {const b=$('letter').getBBox();$('em').setAttribute('x',b.x+b.width/2-500)}
 // centre each small copy in its em, as the font build does
 for(const svg of document.querySelectorAll('#lines svg')){const g=svg.querySelector('.centre'),b=g.getBBox();g.setAttribute('transform',`translate(${500-(b.x+b.width/2)} 0)`)}
 persist();
}
const ACTS={up:(p,s)=>p.mark_dy+=s,down:(p,s)=>p.mark_dy-=s,left:(p,s)=>p.mark_x-=s,right:(p,s)=>p.mark_x+=s,
 bigger:(p,s)=>p.mark_scale=+(p.mark_scale+s/500).toFixed(3),smaller:(p,s)=>p.mark_scale=+(p.mark_scale-s/500).toFixed(3),
 longer:(p,s)=>p.mark_len=+(p.mark_len+s/500).toFixed(3),shorter:(p,s)=>p.mark_len=+(p.mark_len-s/500).toFixed(3),
 thinner:(p,s,f)=>{widen(p,'neck_w',-1,f);widen(p,'head_w',-1,f)},thicker:(p,s,f)=>{widen(p,'neck_w',1,f);widen(p,'head_w',1,f)},
 head_thinner:(p,s,f)=>widen(p,'head_w',-1,f),head_thicker:(p,s,f)=>widen(p,'head_w',1,f),neck_thinner:(p,s,f)=>widen(p,'neck_w',-1,f),neck_thicker:(p,s,f)=>widen(p,'neck_w',1,f),
 kana_lighter:p=>step(p,'kana_bold',BOLDS,-1),kana_heavier:p=>step(p,'kana_bold',BOLDS,1),
 ccw:(p,s)=>p.mark_angle=+(p.mark_angle+s/5).toFixed(1),cw:(p,s)=>p.mark_angle=+(p.mark_angle-s/5).toFixed(1),
 head_ccw:(p,s)=>p.head_angle+=s/2,head_cw:(p,s)=>p.head_angle-=s/2,tail_ccw:(p,s)=>p.tail_angle+=s/2,tail_cw:(p,s)=>p.tail_angle-=s/2,
 bend_left:(p,s)=>p.mark_bend-=s,bend_right:(p,s)=>p.mark_bend+=s,slant_left:(p,s)=>p.mark_slant-=s,slant_right:(p,s)=>p.mark_slant+=s,
 kana_narrower:(p,s,f)=>p.kana_sx=+(p.kana_sx-(f?.005:.02)).toFixed(3),kana_wider:(p,s,f)=>p.kana_sx=+(p.kana_sx+(f?.005:.02)).toFixed(3),
 kana_shorter:(p,s,f)=>p.kana_sy=+(p.kana_sy-(f?.005:.02)).toFixed(3),kana_taller:(p,s,f)=>p.kana_sy=+(p.kana_sy+(f?.005:.02)).toFixed(3),
 kana_smaller:(p,s,f)=>{for(const k of ['kana_sx','kana_sy'])p[k]=+(p[k]-(f?.005:.02)).toFixed(3)},kana_larger:(p,s,f)=>{for(const k of ['kana_sx','kana_sy'])p[k]=+(p[k]+(f?.005:.02)).toFixed(3)},
 reset:p=>Object.assign(p,START)};
// kana steps move along the drawn grid, past any width and weight that could not be drawn
function step(p,key,grid,dir){let i=grid.findIndex(v=>Math.abs(v-p[key])<1e-6);const was=p[key];
 do{i+=dir;if(i<0||i>=grid.length){p[key]=was;return}p[key]=grid[i]}while(!kanaOf(p))}
// widths and weights come in the steps drawn for this page
// widths change by 5% a press (1% with Shift), from a fifth to three times Noto's
function widen(p,key,dir,fine){p[key]=+Math.min(3,Math.max(.2,p[key]+dir*(fine?.01:.05))).toFixed(2)}
function act(name,fine){ACTS[name](state.p,fine?2:10,fine);render()}
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'||e.ctrlKey||e.metaKey||e.altKey)return;
 const name={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right','+':'bigger','=':'bigger','-':'smaller',']':'longer','[':'shorter',',':'thinner','.':'thicker',';':'kana_lighter',"'":'kana_heavier','<':'kana_narrower','>':'kana_wider','{':'kana_shorter','}':'kana_taller',q:'ccw',e:'cw',Q:'ccw',E:'cw',z:'bend_left',c:'bend_right',Z:'bend_left',C:'bend_right',a:'slant_left',d:'slant_right',A:'slant_left',D:'slant_right',w:'head_ccw',r:'head_cw',W:'head_ccw',R:'head_cw',x:'tail_ccw',v:'tail_cw',X:'tail_ccw',V:'tail_cw'}[e.key];
 if(name){e.preventDefault();act(name,e.shiftKey)}});
$('copy').onclick=async()=>{const text=JSON.stringify({arena:EXPERIMENT,protocol:'tune-v1',params:state.p,notes:$('notes').value});
 try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
// one row per control: − / value / +; the rows are the only place the values show
const STEPPERS=[
 [null,'Position'],
 ['x','Left / right',['left','right'],p=>p.mark_x.toFixed(0)],
 ['y','Down / up',['down','up'],p=>p.mark_dy.toFixed(0)],
 [null,'Shape'],
 ['size','Size',['smaller','bigger'],p=>p.mark_scale.toFixed(3)],
 ['len','Length',['shorter','longer'],p=>p.mark_len.toFixed(3)],
 ['angle','Rotate',['cw','ccw'],p=>p.mark_angle.toFixed(1)+'°'],
 ['bend','Bow',['bend_left','bend_right'],p=>p.mark_bend.toFixed(0)],
 ['slant','Slant',['slant_left','slant_right'],p=>p.mark_slant.toFixed(0)],
 ['head_a','Head angle',['head_cw','head_ccw'],p=>p.head_angle.toFixed(0)+'°'],
 ['tail_a','Tail angle',['tail_cw','tail_ccw'],p=>p.tail_angle.toFixed(0)+'°'],
 [null,'Thickness'],
 ['width','Whole stroke',['thinner','thicker'],p=>((p.neck_w+p.head_w)/2).toFixed(2)],
 ['head','Head',['head_thinner','head_thicker'],p=>p.head_w.toFixed(2)],
 ['foot','Foot',['neck_thinner','neck_thicker'],p=>p.neck_w.toFixed(2)],
 [null,'Kana'],
 ['kw',`${KANA} weight`,['kana_lighter','kana_heavier'],p=>String(p.kana_bold)],
 ['ksize',`${KANA} size`,['kana_smaller','kana_larger'],p=>((p.kana_sx+p.kana_sy)/2).toFixed(3)],
 ['ks',`${KANA} width`,['kana_narrower','kana_wider'],p=>p.kana_sx.toFixed(3)],
 ['kh',`${KANA} height`,['kana_shorter','kana_taller'],p=>p.kana_sy.toFixed(3)],
];
$('steppers').innerHTML=STEPPERS.map(([key,label,acts])=>key
 ?`<label for="v-${key}">${label}</label><button type="button" data-act="${acts[0]}" aria-label="${label}: less">−</button><output id="v-${key}"></output><button type="button" data-act="${acts[1]}" aria-label="${label}: more">+</button>`
 :`<span class="group">${label}</span>`).join('');
document.querySelectorAll('[data-act]').forEach(b=>b.onclick=e=>act(b.dataset.act,e.shiftKey));
render();
