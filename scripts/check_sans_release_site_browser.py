"""Exercise the Sans release's Okinawan input and actual glyph fonts."""
import json,re,shutil,subprocess
from pathlib import Path
from check_serif_browsers import stage_dir,q,remaining
from sources import ROOT
from sans_okinawan_release import FULL,digest


def check():
    win,stage=stage_dir('genzui-sans-release-site-check')
    out=ROOT/'build/release'
    registry=json.loads((Path.home()/'.config/genzui/windows-browsers.json').read_text(encoding='utf-8-sig'))
    s=(ROOT/'scripts/browser/serif-chromium.ps1').read_text().replace('__ROOT__',q(win)).replace('__BINARY__',q(registry['chrome.exe']['path'])).replace('__EXTRA__','').replace('__PAGE__',q('http://localhost:8790/genzui-sans-release-site/sans.html'))
    a=s.index(' $report=@{}');b=s.index(' $report.version=',a)
    js=(ROOT/'scripts/okinawan_browser_checks.js').read_text()
    body=" $report=Evaluate '({status:\"passed\",input:null,fonts:0,mobile:null,version:null})'\n $report.input=Evaluate @'\n"+js+"\n'@\n"
    body+=''' Evaluate '(()=>{const data=JSON.parse(document.getElementById("okinawan-data").textContent);for(const weight of [400,700])for(const [i,e] of data.characters.entries()){const p=document.createElement("span");p.className="face release-probe";p.id="release-"+weight+"-"+i;p.style.fontWeight=weight;p.style.fontSize="48px";p.textContent=e.output.map(cp=>String.fromCodePoint(parseInt(cp,16))).join("");document.body.append(p)}return document.fonts.ready.then(()=>true)})()'|Out-Null
 $doc=Call-CDP 'DOM.getDocument'
 foreach($probe in (Evaluate '[...document.querySelectorAll(".release-probe")].map(e=>e.id)')){
  $node=Call-CDP 'DOM.querySelector' @{nodeId=$doc.root.nodeId;selector=('#'+$probe)}
  $fonts=@((Call-CDP 'CSS.getPlatformFontsForNode' @{nodeId=$node.nodeId}).fonts)
  if($fonts.Count -eq 0){throw 'No rendered font'}
  foreach($font in $fonts){if($font.familyName -ne 'GenZui Sans'){throw ('Fallback: '+$font.familyName)}}
  $report.fonts++
 }
 Evaluate '[...document.querySelectorAll(".release-probe")].forEach(e=>e.remove())'|Out-Null
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=390;height=1000;deviceScaleFactor=1;mobile=$false}|Out-Null
 $report.mobile=Evaluate '(()=>{if(document.documentElement.scrollWidth>390)throw Error("overflow");const r=document.getElementById("okinawan").getBoundingClientRect();if(r.left<0||r.right>390)throw Error("composer width");return "passed"})()'
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1200;deviceScaleFactor=1;mobile=$false}|Out-Null
 Evaluate 'document.getElementById("okinawan").scrollIntoView({behavior:"instant"});new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))'|Out-Null
'''
    s=s[:a]+body+s[b:]
    try:
        (stage/'check.ps1').write_text(s,encoding='utf-8-sig')
        r=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',win+'\\check.ps1'],capture_output=True,text=True,timeout=180)
        if r.returncode:
            (ROOT/'build/sans-site-browser-error.txt').write_text(re.sub(r'(?i)(?:/home/|[A-Z]:[\\/]+Users[\\/]+)[^\\/\s]+','~',r.stdout+r.stderr))
            raise RuntimeError('Sans site browser check failed; inspect build/sans-site-browser-error.txt')
        remaining(win)
        report=json.loads((stage/'report.json').read_text(encoding='utf-8-sig'))
        report['font_sha256']={style:digest(FULL/f'GenZuiSans-{style}.woff2') for style in ('Regular','Bold')}
        (ROOT/'research/sans-release-browser-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        shutil.copy2(stage/'proof.png',ROOT/'build/sans-release-site-proof.png')
        print(f'Sans page: {len(report["input"])} input checks, {report["fonts"]} font probes, mobile layout passed.')
    finally:shutil.rmtree(stage)

if __name__=='__main__':check()
