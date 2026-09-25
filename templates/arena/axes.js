'use strict';
// One factor at a time: AXES lists rows of variants that differ from a common base in one
// factor only, in order. The viewer picks the best step per row and may mark steps as
// unacceptable; nothing else is compared, so a vote says which value of which factor won.
const $=id=>document.getElementById(id), storageKey='axes:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,best:{},bad:{},size:32,dark:false,notes:''};
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('saved').textContent='Saved in this browser'}catch{$('saved').textContent='Browser storage unavailable — copy the result before closing'}}
function build(){
 document.body.style.setProperty('--size',state.size+'px');
 $('axes').innerHTML=AXES.map(a=>`<section class="axis" data-axis="${a.key}"><h2>${a.label}</h2><p class="axis-note">${a.note}</p><div class="steps-row">${a.steps.map((t,i)=>t?`<article class="panel step" data-token="${t}" style="--face:${t}"><div class="step-head"><span>${i-3>0?'+':''}${i-3}</span><button type="button" class="bad">Unacceptable</button></div><div class="kana big">${LETTER}</div><div class="kana text">${BIG}</div></article>`:'<article class="panel step empty"><small>not buildable</small></article>').join('')}</div></section>`).join('');
 paint();
}
function paint(){
 for(const a of AXES){
  for(const card of document.querySelectorAll(`.axis[data-axis="${a.key}"] .step[data-token]`)){
   const t=card.dataset.token;
   card.classList.toggle('chosen',state.best[a.key]===t);
   card.classList.toggle('rejected',!!state.bad[a.key]?.includes(t));
   card.querySelector('.bad').textContent=state.bad[a.key]?.includes(t)?'Acceptable':'Unacceptable';
  }
 }
 const done=AXES.filter(a=>state.best[a.key]).length;$('status').textContent=`${done} of ${AXES.length} rows chosen`;
 persist();
}
$('axes').onclick=e=>{
 const card=e.target.closest('.step[data-token]');if(!card)return;
 const axis=card.closest('.axis').dataset.axis,t=card.dataset.token;
 if(e.target.classList.contains('bad')){const list=new Set(state.bad[axis]||[]);list.has(t)?list.delete(t):list.add(t);state.bad[axis]=[...list];if(state.best[axis]===t&&list.has(t))delete state.best[axis]}
 else{state.best[axis]=state.best[axis]===t?undefined:t;if(!state.best[axis])delete state.best[axis]}
 paint();
};
$('size').value=state.size;$('size').onchange=e=>{state.size=Number(e.target.value);build()};
$('dark').checked=state.dark;document.body.classList.toggle('dark',state.dark);$('dark').onchange=e=>{state.dark=e.target.checked;document.body.classList.toggle('dark',state.dark);persist()};
$('notes').value=state.notes;$('notes').oninput=e=>{state.notes=e.target.value;persist()};
function result(){return {arena:EXPERIMENT,protocol:'axes-v1',best:Object.fromEntries(AXES.map(a=>[a.key,state.best[a.key]?a.steps.indexOf(state.best[a.key])-3:null])),unacceptable:Object.fromEntries(AXES.map(a=>[a.key,(state.bad[a.key]||[]).map(t=>a.steps.indexOf(t)-3).sort((x,y)=>x-y)])),notes:state.notes}}
$('copy').onclick=async()=>{const text=JSON.stringify(result());try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
build();
