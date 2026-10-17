# Run in a CDP harness after opening the home page.
# Call-CDP and Evaluate are supplied by the harness. Exercise native browser
# composition: synthetic CompositionEvents do not reproduce its cancellation.
Evaluate @'
(() => {
 const system=document.getElementById('okinawan-system'), method=document.getElementById('okinawan-method');
 system.value='funatsu'; system.dispatchEvent(new Event('change'));
 method.value='kana'; method.dispatchEvent(new Event('change'));
 const source=document.getElementById('okinawan-source');
 source.value='か';source.focus();source.setSelectionRange(1,1);source.dispatchEvent(new Event('input'));
 return true;
})()
'@ | Out-Null
Call-CDP 'Input.imeSetComposition' @{text='とぅ';selectionStart=2;selectionEnd=2} | Out-Null
$loc=Evaluate '(()=>{document.querySelector(".okinawan-key").scrollIntoView({block:"center",behavior:"instant"});const r=document.querySelector(".okinawan-key").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()'
Call-CDP 'Input.dispatchMouseEvent' @{type='mousePressed';x=$loc.x;y=$loc.y;button='left';clickCount=1} | Out-Null
Call-CDP 'Input.dispatchMouseEvent' @{type='mouseReleased';x=$loc.x;y=$loc.y;button='left';clickCount=1} | Out-Null
Call-CDP 'Input.insertText' @{text='とぅ'} | Out-Null
$result=Evaluate @'
(() => {
 const source=document.getElementById('okinawan-source'), output=document.getElementById('okinawan-output');
 const input=OkinawanInput.createInput(JSON.parse(document.getElementById('okinawan-data').textContent));
 if(output.value!==input.convert(source.value,'funatsu','kana').text)throw new Error('Stale output after native IME composition');
 source.value+='てぃ';source.dispatchEvent(new Event('input'));
 if(output.value!==input.convert(source.value,'funatsu','kana').text)throw new Error('Input remained latched in composition');
 if(document.getElementById('okinawan-copy').disabled)throw new Error('Copy remained disabled');
 return {status:'passed',native_composition:true,palette_click:true,subsequent_input:true};
})()
'@
$result
