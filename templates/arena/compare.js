'use strict';
// Pairwise comparison of the forms a cull kept. Each question shows two forms in the same
// passage; the next pair is chosen between forms whose current scores are close and that
// have not met yet. Scores are Bradley–Terry strengths refitted after every vote. One
// decisive pair is asked again later with the sides reversed, as a consistency check.
const $=id=>document.getElementById(id), storageKey='compare:'+EXPERIMENT;
const REASONS=[['mark','Mark position or length'],['turn','Turn into the arm'],['weight','Too thin / too heavy'],['balance','Balance of the whole letter'],['other','Something else']];
let state;try{state=JSON.parse(localStorage.getItem(storageKey));if(state?.experiment!==EXPERIMENT)state=null}catch{}
state??={experiment:EXPERIMENT,votes:[],pair:null,repeat:null,size:32,dark:false,passage:0,pendingReason:null};
function persist(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('saved').textContent='Saved in this browser'}catch{$('saved').textContent='Browser storage unavailable — copy the result before closing'}}
// Bradley–Terry strengths by minorisation–maximisation; a tie counts half a win each way,
// "neither" is recorded but carries no preference.
function strengths(){
 const n=CANDIDATES.length,idx=Object.fromEntries(CANDIDATES.map((c,i)=>[c,i])),w=Array(n).fill(0.5),games=Array.from({length:n},()=>Array(n).fill(0));
 for(const v of state.votes){if(v.outcome==='neither')continue;const a=idx[v.left],b=idx[v.right];games[a][b]++;games[b][a]++;
  if(v.outcome==='left')w[a]+=1;else if(v.outcome==='right')w[b]+=1;else{w[a]+=.5;w[b]+=.5}}
 let p=Array(n).fill(1);
 for(let it=0;it<200;it++){const q=p.map((pi,i)=>{let d=0;for(let j=0;j<n;j++)if(games[i][j])d+=games[i][j]/(pi+p[j]);return d?w[i]/d:pi});const s=q.reduce((a,b)=>a+b,0)/n;p=q.map(x=>x/s)}
 return Object.fromEntries(CANDIDATES.map((c,i)=>[c,p[i]]));
}
function met(a,b){return state.votes.some(v=>(v.left===a&&v.right===b)||(v.left===b&&v.right===a))}
function nextPair(){
 const decisive=state.votes.filter(v=>(v.outcome==='left'||v.outcome==='right')&&!v.repeat);
 if(!state.repeat&&decisive.length>=8){const v=decisive[Math.floor(decisive.length/2)];state.repeat={left:v.right,right:v.left,of:state.votes.indexOf(v)};return {left:v.right,right:v.left,repeat:true}}
 const s=strengths(),counts=Object.fromEntries(CANDIDATES.map(c=>[c,0]));
 for(const v of state.votes){counts[v.left]++;counts[v.right]++}
 const order=[...CANDIDATES].sort((a,b)=>counts[a]-counts[b]||Math.random()-.5);
 for(const a of order){
  const others=CANDIDATES.filter(b=>b!==a&&!met(a,b)).sort((x,y)=>Math.abs(Math.log(s[x]/s[a]))-Math.abs(Math.log(s[y]/s[a])));
  if(others.length){const b=others[0];return Math.random()<.5?{left:a,right:b}:{left:b,right:a}}
 }
 return null;
}
function show(){
 document.body.style.setProperty('--size',state.size+'px');
 state.pair??=nextPair();persist();
 const pair=state.pair;
 $('progress').textContent=`${state.votes.length} judgments`;
 if(!pair){$('panels').hidden=true;$('done').hidden=false;return}
 for(const side of ['left','right']){
  const panel=$(side);panel.style.setProperty('--face',pair[side]);
  panel.querySelector('.big').innerHTML=BIG;
  panel.querySelector('.text').innerHTML=PASSAGES[state.passage];
  panel.querySelector('.v').innerHTML=VERTICAL;
 }
 renderResult();
}
function vote(outcome){
 const pair=state.pair;if(!pair)return;
 state.votes.push({left:pair.left,right:pair.right,outcome,passage:state.passage,repeat:!!pair.repeat,reason:null,at:new Date().toISOString()});
 state.pair=null;state.passage=(state.passage+1)%PASSAGES.length;
 $('reasons').hidden=!(outcome==='left'||outcome==='right'||outcome==='neither');
 show();
}
function reason(key){const v=state.votes[state.votes.length-1];if(v){v.reason=key;persist()}$('reasons').hidden=true}
function renderResult(){
 const s=strengths(),ranked=[...CANDIDATES].sort((a,b)=>s[b]-s[a]);
 $('ranking').innerHTML=ranked.slice(0,6).map((c,i)=>`<li><span class="kana leader-glyph" style="--face:${c}">${BIG}</span><small>${i+1}. strength ${s[c].toFixed(2)}</small></li>`).join('');
}
function result(){const s=strengths();return {arena:EXPERIMENT,protocol:'pairwise-bt-v1',strengths:Object.fromEntries(Object.entries(s).sort((a,b)=>b[1]-a[1]).map(([k,v])=>[k,+v.toFixed(3)])),votes:state.votes}}
$('size').value=state.size;$('size').onchange=e=>{state.size=Number(e.target.value);show()};
$('dark').checked=state.dark;document.body.classList.toggle('dark',state.dark);$('dark').onchange=e=>{state.dark=e.target.checked;document.body.classList.toggle('dark',state.dark);persist()};
for(const [id,outcome] of [['vote-left','left'],['vote-right','right'],['vote-tie','tie'],['vote-neither','neither']])$(id).onclick=()=>vote(outcome);
$('reasons').innerHTML=REASONS.map(([k,l])=>`<button type="button" data-k="${k}">${l}</button>`).join('')+'<button type="button" data-k="">Skip</button>';
$('reasons').onclick=e=>{const k=e.target.dataset?.k;if(k!==undefined)reason(k||null)};
$('undo').onclick=()=>{if(state.votes.length){const v=state.votes.pop();if(v.repeat)state.repeat=null;state.pair={left:v.left,right:v.right,repeat:v.repeat};$('reasons').hidden=true;show()}};
$('copy').onclick=async()=>{const text=JSON.stringify(result());try{await navigator.clipboard.writeText(text);$('copy-status').textContent='Copied. Paste it into the conversation.'}catch{prompt('Copy this result:',text)}};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;({ArrowLeft:()=>vote('left'),ArrowRight:()=>vote('right'),ArrowUp:()=>vote('tie'),ArrowDown:()=>vote('neither')})[e.key]?.()});
show();
