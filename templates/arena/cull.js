'use strict';
// Culling: all forms of the round on one page, each with a reject toggle. The rejected ids
// are stored in this browser under cull:<experiment> and copied out as the result.
const $=id=>document.getElementById(id), storageKey='cull:'+EXPERIMENT;
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,rejected:[],order:null,size:24,passage:0,dark:false,done:false,notes:''};
state.order??=shuffle([...CANDIDATES]);
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
// Keep previous studies intact if browser storage is full.
function persist(){
 try{localStorage.setItem(storageKey,JSON.stringify(state))}
 catch{$('saved').textContent='Browser storage unavailable — copy the result before closing';return}
 $('saved').textContent='Saved in this browser';
}
const rejected=new Set(state.rejected);
function status(){const kept=CANDIDATES.length-rejected.size;const s=`${rejected.size} rejected · ${kept} kept of ${CANDIDATES.length}`;$('status').textContent=s;$('progress').textContent=s;}
function build(){
 const grid=$('grid');grid.innerHTML='';
 state.order.forEach((id,i)=>{
  const card=document.createElement('article');card.className='panel card'+(rejected.has(id)?' rejected':'');card.style.setProperty('--face',id);card.dataset.id=id;
  card.innerHTML=`<div class="panel-heading"><h2>Form ${i+1} <span class="verdict"></span></h2><button type="button" class="reject"></button></div><div class="kana big">${BIG}</div><div class="body"><div class="kana text"></div><div class="kana v"></div></div>`;
  card.onclick=()=>toggle(id);
  grid.appendChild(card);
 });
 fill();for(const id of state.order)paint(id);
}
function paint(id){const card=document.querySelector(`.card[data-id="${id}"]`);const r=rejected.has(id);card.classList.toggle('rejected',r);card.querySelector('.reject').textContent=r?'Keep':'Reject';card.querySelector('.verdict').textContent=r?'· rejected':''}
function fill(){
 document.body.style.setProperty('--size',state.size+'px');
 for(const card of document.querySelectorAll('.card')){card.querySelector('.text').innerHTML=PASSAGES[state.passage];card.querySelector('.v').innerHTML=VERTICAL}
}
function toggle(id){
 if(rejected.has(id))rejected.delete(id);else rejected.add(id);
 state.rejected=[...rejected];state.done=false;paint(id);status();persist();
}
const sel=$('passage');PASSAGE_LABELS.forEach((l,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1}. ${l}`;sel.appendChild(o)});sel.value=state.passage;
sel.onchange=e=>{state.passage=Number(e.target.value);fill();persist()};
$('size').value=state.size;$('size').onchange=e=>{state.size=Number(e.target.value);fill();persist()};
$('dark').checked=state.dark;document.body.classList.toggle('dark',state.dark);$('dark').onchange=e=>{state.dark=e.target.checked;document.body.classList.toggle('dark',state.dark);persist()};
$('shuffle').onclick=()=>{state.order=shuffle([...state.order]);build();persist()};
$('clear').onclick=()=>{if(!rejected.size||confirm('Clear all rejections?')){rejected.clear();state.rejected=[];state.done=false;build();status();persist()}};
function result(){return {arena:EXPERIMENT,protocol:'cull-v1',kept:CANDIDATES.filter(id=>!rejected.has(id)),rejected:[...rejected],size:state.size,passage:state.passage,notes:state.notes||''}}
$('notes').value=state.notes||'';$('notes').oninput=e=>{state.notes=e.target.value;persist()};
$('copy').onclick=async()=>{const text=JSON.stringify(result());try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
build();status();persist();
