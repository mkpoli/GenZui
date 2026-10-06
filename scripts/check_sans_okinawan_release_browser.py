"""Check the actual full/subset public specimens with Windows Chrome."""
import json,re,shutil,subprocess
from pathlib import Path
from check_serif_browsers import stage_dir,q,remaining
from sans_okinawan_release import FULL,SUB,VERSION,PREFIX,digest


def check():
    registry=json.loads((Path.home()/'.config/genzui/windows-browsers.json').read_text(encoding='utf-8-sig'))
    for folder,prefix,family,slug in [(FULL,'GenZuiSans','GenZui Sans','genzui-sans-release'),(SUB,PREFIX,'GenZui Sans Okinawan','genzui-sans-okinawan-release')]:
        win,stage=stage_dir('genzui-sans-release-check')
        s=Path('scripts/browser/serif-chromium.ps1').read_text()
        s=s.replace('__ROOT__',q(win)).replace('__BINARY__',q(registry['chrome.exe']['path'])).replace('__EXTRA__','').replace('__PAGE__',q(f'http://localhost:8790/{slug}/'))
        a=s.index(' $report=@{}');b=s.index(' $report.version=',a)
        s=s[:a]+''' $report=Evaluate '(()=>{const a=(v,m)=>{if(!v)throw Error(m)};a(document.querySelectorAll(".letters span").length===70,"35 forms per weight");a(document.querySelectorAll("[contenteditable]").length===2,"sentences");document.querySelectorAll(".sample").forEach((e,i)=>e.id="probe"+i);return {status:"passed",forms:35,weights:2,fonts:0,mobile:null,version:null}})()'
 $doc=Call-CDP 'DOM.getDocument'
 foreach($probe in (Evaluate '[...document.querySelectorAll(".sample")].map(e=>e.id)')){
  $node=Call-CDP 'DOM.querySelector' @{nodeId=$doc.root.nodeId;selector=('#'+$probe)}
  $fonts=@((Call-CDP 'CSS.getPlatformFontsForNode' @{nodeId=$node.nodeId}).fonts)
  if($fonts.Count -eq 0){throw 'No rendered font'}
  $expected=Evaluate ('document.getElementById("'+$probe+'").dataset.family')
  foreach($font in $fonts){if($font.familyName -ne $expected){throw ('Fallback: '+$font.familyName)}}
  $report.fonts++
 }
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=390;height=1000;deviceScaleFactor=1;mobile=$false}|Out-Null
 $report.mobile=Evaluate '(()=>{if(document.documentElement.scrollWidth>390)throw Error("overflow");if(getComputedStyle(document.querySelector(".columns")).gridTemplateColumns.split(" ").length!==2)throw Error("columns");return "passed"})()'
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1200;deviceScaleFactor=1;mobile=$false}|Out-Null
'''+s[b:]
        try:
            (stage/'check.ps1').write_text(s,encoding='utf-8-sig')
            r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',win+'\\check.ps1'],capture_output=True,text=True,timeout=140)
            if r.returncode:
                clean=re.sub(r'(?i)(?:/home/|[A-Z]:[\\/]+Users[\\/]+)[^\\/\s]+','~',r.stdout+r.stderr)
                (folder/'browser-error.txt').write_text(clean);raise RuntimeError('Public specimen browser check failed; inspect browser-error.txt')
            remaining(win)
            report=json.loads((stage/'report.json').read_text(encoding='utf-8-sig'));report.update(family=family,release_version=VERSION)
            for style,key in [('Regular',''),('Bold','bold_')]:
                for ext in ('ttf','woff2'):report[key+ext+'_sha256']=digest(folder/f'{prefix}-{style}.{ext}')
            (folder/'browser-checks.json').write_text(json.dumps(report,indent=2)+'\n')
            shutil.copy2(stage/'proof.png',folder/'preview.png')
            (folder/'browser-error.txt').unlink(missing_ok=True)
            print(f'{family}: all35 forms, both weights, native font and mobile layout passed.')
        finally:shutil.rmtree(stage)

if __name__=='__main__':check()
