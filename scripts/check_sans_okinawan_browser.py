"""Verify the local Sans Okinawan proof in Windows Chrome, including mobile layout."""
import sys,json,shutil,subprocess,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_serif_browsers import stage_dir,q,remaining
win,stage=stage_dir('genzui-sans-okinawan-review')
out=Path('build/sans-okinawan')
registry=json.loads((Path.home()/'.config/genzui/windows-browsers.json').read_text(encoding='utf-8-sig'))
s=Path('scripts/browser/serif-chromium.ps1').read_text()
s=s.replace('__ROOT__',q(win)).replace('__BINARY__',q(registry['chrome.exe']['path'])).replace('__EXTRA__','').replace('__PAGE__',q('http://localhost:8790/genzui-sans-okinawan/'))
a=s.index(' $report=@{}');b=s.index(" $report.version=",a)
s=s[:a]+""" Evaluate '(()=>{const d=document.querySelector(".approved-group");if(!d||d.open)throw Error("confirmed group must start collapsed");if(d.querySelectorAll("section[data-form]").length!==29)throw Error("confirmed count");if(document.querySelectorAll("main>section[data-form]").length!==4)throw Error("unresolved count");return true})()'|Out-Null
 Evaluate '[...document.querySelectorAll("details")].forEach(e=>e.open=true)'|Out-Null
 $report=Evaluate '(()=>{const assert=(v,m)=>{if(!v)throw Error(m)};assert(document.querySelectorAll(".we-alternative").length===6,"WE alternatives");assert(document.querySelectorAll(".context").length===70,"all35bothweights");assert(document.querySelectorAll("[contenteditable]").length===4,"sentences");assert(document.querySelectorAll(".serif").length===70,"serif references");assert(document.querySelectorAll(".raised-sample").length===8,"raised samples");document.querySelectorAll(".context,.sentence,.previous,.serif,.raised-sample,.we-alternative").forEach((e,i)=>{e.id="probe"+i});return {status:"passed",forms:35,styles:2,sentences:4,serif:70,confirmed:29,unresolved:4,raised:8,weAlternatives:6,previous:document.querySelectorAll(".previous").length,mobile:null,raisedDpr2:null,version:null,fonts:{verified:0}}})()'
 $doc=Call-CDP 'DOM.getDocument'
 foreach($probe in (Evaluate '[...document.querySelectorAll(".context,.sentence,.previous,.serif,.raised-sample,.we-alternative")].map(e=>e.id)')){
  $node=Call-CDP 'DOM.querySelector' @{nodeId=$doc.root.nodeId;selector=('#'+$probe)}
  $fonts=@((Call-CDP 'CSS.getPlatformFontsForNode' @{nodeId=$node.nodeId}).fonts)
  if($fonts.Count -eq 0){throw ('No rendered font in '+$probe)}
  $report.fonts.verified++
  $expected=Evaluate ('(()=>{const e=document.getElementById("'+$probe+'");return e.dataset.family||(e.classList.contains("serif")?"GenZui Serif Okinawan":"GenZui Sans Okinawan")})()')
  foreach($font in $fonts){if($font.familyName -ne $expected){throw ('Fallback in '+$probe+': '+$font.familyName)}}
 }
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=390;height=1000;deviceScaleFactor=1;mobile=$false}|Out-Null
 $report.mobile=Evaluate '(()=>{if(document.documentElement.scrollWidth>390)throw Error("overflow");if(getComputedStyle(document.querySelector(".columns")).gridTemplateColumns.split(" ").length!==2)throw Error("columns");return "passed"})()'
 Evaluate '[...document.querySelectorAll("details")].forEach(e=>e.open=false)'|Out-Null
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1550;deviceScaleFactor=2;mobile=$false}|Out-Null
 Evaluate 'document.querySelector(".approved-group").open=true;document.getElementById("raised-comparison").scrollIntoView();new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))'|Out-Null
 $report.raisedDpr2=Evaluate '(()=>{if(devicePixelRatio!==2)throw Error("DPR");return "passed"})()'
 $raisedShot=Call-CDP 'Page.captureScreenshot' @{format='png'}
 [IO.File]::WriteAllBytes((Join-Path $root 'raised-2x.png'),[Convert]::FromBase64String($raisedShot.data))
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1550;deviceScaleFactor=1;mobile=$false}|Out-Null
 Evaluate 'document.querySelector(".approved-group").open=false;scrollTo(0,0)'|Out-Null
"""+s[b:]

try:
 (stage/'check.ps1').write_text(s,encoding='utf-8-sig')
 r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',win+'\\check.ps1'],capture_output=True,text=True,timeout=140)
 if r.returncode:
  (out/'browser-error.txt').write_text(re.sub(r'(?i)(?:/home/|[A-Z]:[\\/]+Users[\\/]+)[^\\/\s]+','~',r.stdout+r.stderr))
  raise RuntimeError('Sans Okinawan browser check failed; inspect the local browser-error.txt')
 remaining(win)
 report=json.loads((stage/'report.json').read_text(encoding='utf-8-sig'))
 (out/'browser-check.json').write_text(json.dumps(report,indent=2)+'\n')
 shutil.copyfile(stage/'proof.png',out/'browser-proof.png')
 shutil.copyfile(stage/'raised-2x.png',out/'raised-browser-2x.png')
 (out/'browser-error.txt').unlink(missing_ok=True)
 print(json.dumps(report))
finally:shutil.rmtree(stage)
