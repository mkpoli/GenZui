'use strict';
// Direct placement of the glottal mark beside a kana that stays put. The mark's outline is
// drawn once; placing it is a translation, and its size and length are scalings about its
// foot, the same transforms the font build applies.
const $=id=>document.getElementById(id), storageKey='tune:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,p:{...START}};
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('saved').textContent='Saved in this browser'}catch{$('saved').textContent='Browser storage unavailable — copy the result before closing'}}
function markTransform(p){const [fx,foot]=ORIGIN;
 return `translate(${p.mark_x} ${foot*(1-p.mark_len)+p.mark_dy}) scale(1 ${p.mark_len}) translate(${fx} ${foot}) scale(${p.mark_scale}) translate(${-fx} ${-foot})`}
function glyph(){return `<svg viewBox="0 0 1000 1000" aria-hidden="true"><g class="centre"><g transform="matrix(1 0 0 -1 0 880)"><path class="ink" d="${KANA_D}"/><path class="ink" d="${MARK_D}" transform="${markTransform(state.p)}"/></g></g></svg>`}
function render(){
 const p=state.p;
 $('mark-g').setAttribute('transform',markTransform(p));
 $('values').innerHTML=`<dt>right</dt><dd>${p.mark_x.toFixed(0)}</dd><dt>up</dt><dd>${p.mark_dy.toFixed(0)}</dd><dt>size</dt><dd>${p.mark_scale.toFixed(3)}</dd><dt>length</dt><dd>${p.mark_len.toFixed(3)}</dd>`;
 $('lines').innerHTML=LINES.map(l=>`<p>${l.replaceAll(LETTER,glyph())}</p>`).join('');
 // centre each small copy in its em, as the font build does
 for(const svg of document.querySelectorAll('#lines svg')){const g=svg.querySelector('.centre'),b=g.getBBox();g.setAttribute('transform',`translate(${500-(b.x+b.width/2)} 0)`)}
 persist();
}
const ACTS={up:(p,s)=>p.mark_dy+=s,down:(p,s)=>p.mark_dy-=s,left:(p,s)=>p.mark_x-=s,right:(p,s)=>p.mark_x+=s,
 bigger:(p,s)=>p.mark_scale=+(p.mark_scale+s/500).toFixed(3),smaller:(p,s)=>p.mark_scale=+(p.mark_scale-s/500).toFixed(3),
 longer:(p,s)=>p.mark_len=+(p.mark_len+s/500).toFixed(3),shorter:(p,s)=>p.mark_len=+(p.mark_len-s/500).toFixed(3),
 reset:p=>Object.assign(p,START)};
function act(name,fine){ACTS[name](state.p,fine?2:10);render()}
document.querySelectorAll('[data-act]').forEach(b=>b.onclick=e=>act(b.dataset.act,e.shiftKey));
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT'||e.ctrlKey||e.metaKey||e.altKey)return;
 const name={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right','+':'bigger','=':'bigger','-':'smaller',']':'longer','[':'shorter'}[e.key];
 if(name){e.preventDefault();act(name,e.shiftKey)}});
$('kana').setAttribute('d',KANA_D);$('mark').setAttribute('d',MARK_D);
$('copy').onclick=async()=>{const text=JSON.stringify({arena:EXPERIMENT,protocol:'tune-v1',params:state.p,notes:$('notes').value});
 try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
render();
