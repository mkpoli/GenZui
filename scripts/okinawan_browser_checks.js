(async () => {
  const $ = id => document.getElementById(id);
  const results = [];
  function check(name, condition) { if (!condition) throw new Error(name); results.push(name); }
  const source=$('okinawan-source'), output=$('okinawan-output'), system=$('okinawan-system'), method=$('okinawan-method');
  const data=JSON.parse($('okinawan-data').textContent), input=OkinawanInput.createInput(data);
  const emit=el=>el.dispatchEvent(new Event('input',{bubbles:true}));
  const change=(el,value)=>{el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));};
  const set=value=>{source.value=value;emit(source);};
  change(system,'funatsu'); change(method,'kana');
  check('27 Funatsu palette keys', document.querySelectorAll('.okinawan-key').length===27);
  set('とぅ い\u3099'); check('kana and canonical combining output',output.value==='\uF450 い\u3099');
  source.focus();source.setSelectionRange(0,2);document.querySelector('.okinawan-key').click();
  check('palette replaces selection',source.value==='{tu} い\u3099'&&output.value==='\uF450 い\u3099');
  check('editor focus restored', document.activeElement===source);
  source.dispatchEvent(new CompositionEvent('compositionstart'));
  source.value='てぃ';emit(source);
  check('composition waits for commit',output.value==='\uF450 い\u3099');
  check('composition disables palette and copy',document.querySelector('.okinawan-key').disabled&&$('okinawan-copy').disabled);
  source.dispatchEvent(new CompositionEvent('compositionend'));
  check('composition commit updates result',output.value==='\uF452'&&!$('okinawan-copy').disabled);
  change(method,'romaji');set('shi si chi ti tsu tu');
  check('distinct romaji syllables', output.value==='し \uF467 ち \uF452 つ \uF450');
  const draft=source.value;
  change(system,'prefecture');
  check('8 raised palette keys',document.querySelectorAll('.okinawan-key').length===8);
  change(method,'romaji');set('utu ^uutu');
  check('raised-vowel example',output.value==='ウトゥ \uE534ウトゥ');
  for(const e of data.characters.filter(e=>e.system==='prefecture')) {
    set(e.id+'ア');check(e.id+' plain input',output.value===input.text(e)+'ア');
  }
  set('{tu}');check('wrong-system shortcuts retained',output.value==='{tu}'&&$('okinawan-warning').textContent.includes('Unknown'));
  change(system,'funatsu');check('system draft restored',source.value===draft&&method.value==='romaji');
  set('\uF451\uF464\uF466');check('legacy PUA normalized',output.value==='\uF450\u3099い\u3099え\u3099');
  check('visible output code points',$('okinawan-codepoints').textContent==='U+F450 U+3099 U+3044 U+3099 U+3048 U+3099');
  const clipboard=Object.getOwnPropertyDescriptor(navigator,'clipboard'), exec=document.execCommand;
  let selected='';
  try {
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>Promise.reject(new Error('Test fallback'))}});
    document.execCommand=command=>{selected=document.activeElement.value.slice(document.activeElement.selectionStart,document.activeElement.selectionEnd);return command==='copy';};
    $('okinawan-copy').click();await new Promise(r=>setTimeout(r,0));
    check('copy fallback selects exact plain text',selected===output.value&&$('okinawan-copy-status').textContent==='Copied.');
  } finally { if(clipboard)Object.defineProperty(navigator,'clipboard',clipboard);else delete navigator.clipboard;document.execCommand=exec; }
  $('okinawan-clear').click();check('clear updates result and codepoints',source.value===''&&output.value===''&&$('okinawan-codepoints').textContent==='');
  $('okinawan-example').click();
  document.querySelector('[data-filter="okinawan"]').click();
  check('26 visible PUA inventory entries',document.querySelectorAll('#character-grid .glyph-button').length===26&&!document.querySelector('#character-grid .nonprinting'));
  check('PUA identified as private use',$('detail-age').textContent==='Private use');
  return results;
})()
