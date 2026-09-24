(async () => {
 const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
 await Promise.all(['GenZui','Previous'].map(f=>document.fonts.load('48px '+f,'𛄣𛄟𛄤𛄥')));await document.fonts.ready;
 const checks=[],check=(name,pass)=>{if(!pass)throw new Error(name);checks.push(name)};
 const change=(selector,value)=>{const e=$(selector);e.value=value;e.dispatchEvent(new Event('change',{bubbles:true}))};
 const visible=()=>$$('.glyph-card').filter(e=>!e.hidden);
 const uses=(sample,family)=>[...sample.querySelectorAll('.reading>span')].every(e=>getComputedStyle(e).fontFamily.startsWith(family));
 const feature=e=>getComputedStyle(e).fontFeatureSettings;
 check('11 drawn forms initially',visible().length===11&&visible().every(e=>e.dataset.kind==='drawn'));
 check('21 constructions total',$$('.glyph-card').length===21);
 check('unique character cards',new Set($$('.glyph-card').map(e=>e.id)).size===21);
 check('both proof fonts loaded',[...document.fonts].length===2&&[...document.fonts].every(f=>f.status==='loaded'));
 change('#collection','revised');check('only TOKI and TOTE revised',visible().map(e=>e.id).sort().join(',')==='u1b124,u1b125');
 change('#collection','small');check('ten small adaptations',visible().length===10);
 change('#collection','all');check('all constructions visible',visible().length===21);
 check('both writing directions on every sample',$$('.sample').every(e=>e.querySelector('.horizontal-reading')&&e.querySelector('.vertical-reading')));
 check('vertical writing mode',$$('.vertical-reading').every(e=>getComputedStyle(e).writingMode==='vertical-rl'&&getComputedStyle(e).textOrientation==='mixed'));
 check('horizontal writing mode',$$('.horizontal-reading').every(e=>getComputedStyle(e).writingMode==='horizontal-tb'));
 for(const cp of ['1b11f','1b123','1b126','2a708','2cf00','2ceff','1b128']){
  const card=$('#u'+cp);
  check('accepted '+cp+' displayed once',card.querySelectorAll('.sample').length===1&&!!card.querySelector('.approved')&&!card.querySelector('.swap')&&!card.querySelector('.overlay-old'));
 }
 check('superseded KOTO studies removed',!$('.candidate')&&!$('#koto-candidates'));
 check('KOTO context includes TO and WO',$('#u1b123 .horizontal-reading').textContent.includes('と𛄣を')&&$('#u1b123 .vertical-reading').textContent.includes('と𛄣を'));
 check('TOMO beside TOKI and TOTE in both modes',$$('#u2a708 .reading').every(e=>e.textContent.includes('𛄤𪜈𛄥')));
 for(const cp of ['1b124','1b125'])check(cp+' with TOMO in both directions',$$('#u'+cp+' .reading').every(e=>e.textContent.includes('𪜈𛄥𛄤')));
 check('native stroke studies for TOMO and NARI',$$('#u2a708 .stroke-study svg').length===3&&$$('#u2cf02 .stroke-study svg').length===2);
 check('curved WU default',$('#wu-style').value==='curved'&&!document.body.classList.contains('hooked-on'));
 check('curved WU shown once',$$('#u1b11f .sample').length===1&&!$('#u1b11f .swap'));
 check('fixed WU feature assignments',feature($('.wu-fixed.curved'))==='"ss01" 0'&&feature($('.wu-fixed.hooked'))==='"ss01"');
 change('#wu-style','hooked');
 check('hooked selection description',$('#wu-setting').textContent==='Hooked WU · ss01 on');
 check('hooked WU in both writing directions',$$('#u1b11f .current .reading').every(e=>feature(e)==='"ss01"'));
 check('hooked outline selected',getComputedStyle($('#u1b11f .current .default-shape')).display==='none'&&getComputedStyle($('#u1b11f .current .alternate-shape')).display!=='none');
 $('#overlay').click();
 check('previous TOKI and TOTE overlays visible',['1b124','1b125'].every(cp=>getComputedStyle($('#u'+cp+' .overlay-old')).display!=='none'));
 $('#overlay').click();
 check('native WU hook references',$$('#u1b11f .stroke-study svg').length===2);
 check('retained NE shown once',$$('#u1b127 .sample').length===1&&!$('#u1b127 .swap'));
 for(const button of $$('.glyph-card .swap')){
  const sample=button.closest('.sample'),id=sample.closest('.glyph-card').id;
  const height=sample.getBoundingClientRect().height;button.click();
  check(id+' swaps drawing and both contexts',button.getAttribute('aria-pressed')==='true'&&sample.querySelector('.version-label').textContent==='0.111'&&uses(sample,'Previous')&&getComputedStyle(sample.querySelector('.previous-outline')).display!=='none');
  check(id+' keeps comparison position',Math.abs(sample.getBoundingClientRect().height-height)<1);
  if(id==='u1b11f')check('swapped WU stays hooked',feature(sample.querySelector('.reading'))==='"ss01"');
  button.click();check(id+' restores current',!sample.classList.contains('is-previous')&&uses(sample,'GenZui')&&sample.querySelector('.version-label').textContent==='0.117');
 }
 change('#wu-style','curved');
 check('return to curved clears previous state',!$('#u1b11f .current').classList.contains('is-previous')&&getComputedStyle($('#u1b11f .current .default-shape')).display!=='none'&&getComputedStyle($('#u1b11f .current .alternate-shape')).display==='none');
 $('#guides').click();check('guides hide',getComputedStyle($('#u1b124 .guides')).visibility==='hidden');$('#guides').click();
 $('#reading-size').value=72;$('#reading-size').dispatchEvent(new Event('input',{bubbles:true}));
 check('size changes both directions',getComputedStyle($('#u1b124 .horizontal-reading')).fontSize==='72px'&&getComputedStyle($('#u1b124 .vertical-reading')).fontSize==='72px');
 $('#reading-size').value=40;$('#reading-size').dispatchEvent(new Event('input',{bubbles:true}));
 check('two historical NARI scans',$$('.historical-reference img').length===2&&$$('.historical-reference a').every(a=>a.href.startsWith('https://dl.ndl.go.jp/pid/')));
 check('current download',$('footer a[href$=".zip"]').href.includes('GenZuiSerif-0.117.zip'));
 check('no page overflow',document.documentElement.scrollWidth<=innerWidth);
 // Execute the real fallback userscript, then inspect each leaf text node.
 const fixture=document.createElement('p');fixture.textContent='𛄣';document.body.append(fixture);
 const styles=[],oldAddStyle=window.GM_addStyle;
 window.GM_addStyle=css=>{const e=document.createElement('style');e.textContent=css;document.head.append(e);styles.push(e);return e};
 const script=document.createElement('script');script.src='browser/historical-kana-fallback.user.js';
 const settle=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 try{
  await new Promise((resolve,reject)=>{script.onload=resolve;script.onerror=reject;document.head.append(script)});await settle();
  check('fallback active on ordinary text',getComputedStyle(fixture).fontFamily.includes('Historical Kana Local Fallback'));
  check('fixed WU and native references retain GenZui',$$('.wu-fixed,.native').every(e=>getComputedStyle(e).fontFamily.startsWith('GenZui')));
  change('#wu-style','hooked');
  for(const button of $$('.glyph-card .swap')){
   const sample=button.closest('.sample'),id=sample.closest('.glyph-card').id;
   button.click();await settle();check(id+' swaps text with fallback active',uses(sample,'Previous'));
   if(id==='u1b11f')check('fallback preserves old hooked feature',feature(sample.querySelector('.reading>span'))==='"ss01"');
   button.click();await settle();check(id+' restores text with fallback active',uses(sample,'GenZui'));
   if(id==='u1b11f')check('fallback preserves new hooked feature',feature(sample.querySelector('.reading>span'))==='"ss01"');
  }
  for(const card of $$('.glyph-card:has(.single)'))check(card.id+' single specimen keeps GenZui',uses(card,'GenZui'));
  check('fallback still active elsewhere',getComputedStyle(fixture).fontFamily.includes('Historical Kana Local Fallback'));
 }finally{fixture.remove();script.remove();styles.forEach(e=>e.remove());if(oldAddStyle===undefined)delete window.GM_addStyle;else window.GM_addStyle=oldAddStyle;}
 change('#wu-style','curved');change('#collection','drawn');
 return checks;
})()
