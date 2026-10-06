"""Exercise the local audit report in Chrome, including its actual fonts."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from check_serif_browsers import stage_dir, q, remaining

OUT = Path('build/sans-weight-audit')


def check():
    win, stage = stage_dir('genzui-sans-weight-audit')
    registry = json.loads((Path.home()/'.config/genzui/windows-browsers.json').read_text(encoding='utf-8-sig'))
    template = Path('scripts/browser/serif-chromium.ps1').read_text()
    template = template.replace('__ROOT__',q(win)).replace('__BINARY__',q(registry['chrome.exe']['path'])).replace('__EXTRA__','').replace('__PAGE__',q('http://localhost:8790/genzui-sans-weight-audit/'))
    a,b = template.index(' $report=@{}'),template.index(' $report.version=')
    checks = r'''
 Evaluate 'new Promise((resolve,reject)=>{let tries=0;const t=setInterval(()=>{if(document.documentElement.dataset.ready){clearInterval(t);resolve(true)}else if(tries++>60){clearInterval(t);reject(Error("report timeout"))}},100)})'|Out-Null
 $report=Evaluate '(()=>{const assert=(v,m)=>{if(!v)throw Error(m)};assert(document.querySelectorAll("article").length===70,"70 cards");assert(document.querySelectorAll(".pair").length===35,"35 paired forms");assert(document.querySelectorAll("#all tbody tr").length===375,"375 forms");document.querySelector("[data-style=Bold]").click();assert(document.querySelector("article .family .muted").textContent==="Bold","weight control");document.querySelector("#search").value="HWE";document.querySelector("#search").dispatchEvent(new Event("input"));assert(document.querySelectorAll("#all tbody tr").length===1,"search");document.querySelector("#search").value="";document.querySelector("#search").dispatchEvent(new Event("input"));const before=document.querySelector(".measure strong").textContent;document.querySelector("#metric").value="q50";document.querySelector("#metric").dispatchEvent(new Event("change"));assert(document.querySelector(".measure strong").textContent!==before,"metric control");return {status:"passed",cards:70,pairs:35,forms:375,controls:"passed",fonts:[],mobile:null,version:null}})()'
 foreach($style in @('Regular','Bold')){
  Evaluate ('document.querySelector("[data-style='+$style+']").click();document.querySelector("article.Sans .target").id="sans-probe";document.querySelector("article.Serif .target").id="serif-probe";true')|Out-Null
  Evaluate 'Promise.all([...document.fonts].map(f=>f.load())).then(()=>document.fonts.ready).then(()=>true)'|Out-Null
  $changed=Evaluate '(async()=>{if(document.querySelector("#edition-label").hidden)return null;await document.fonts.load("160px GZSans");await document.fonts.load("160px GZRevised");const ink=family=>{const c=document.createElement("canvas");c.width=220;c.height=240;const x=c.getContext("2d");x.font="160px "+family;x.fillText(String.fromCodePoint(0xF458),25,180);const a=x.getImageData(0,0,220,240).data;let sum=0;for(let i=3;i<a.length;i+=4)sum+=a[i];return sum};const before=ink("GZSans"),after=ink("GZRevised");if(!(after<before))throw Error("revised KWE ink not lighter");return true})()'
 $doc=Call-CDP 'DOM.getDocument'
  foreach($family in @('Sans','Serif')){
   $node=Call-CDP 'DOM.querySelector' @{nodeId=$doc.root.nodeId;selector=('#'+$family.ToLower()+'-probe')}
   $fonts=@((Call-CDP 'CSS.getPlatformFontsForNode' @{nodeId=$node.nodeId}).fonts)
   if($fonts.Count -ne 1 -or $fonts[0].familyName -ne ('GenZui '+$family) -or $fonts[0].postScriptName -ne ('GenZui'+$family+'-'+$style)){throw 'Unexpected specimen font'}
   $report.fonts+=@{family=$family;style=$style;postScriptName=$fonts[0].postScriptName}
  }
 }
 Evaluate 'document.querySelector("[data-style=Regular]").click();document.querySelector("#metric").value="q75";document.querySelector("#metric").dispatchEvent(new Event("change"));true'|Out-Null
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=390;height=1000;deviceScaleFactor=1;mobile=$false}|Out-Null
 $report.mobile=Evaluate '(()=>{if(document.documentElement.scrollWidth>390)throw Error("mobile overflow");const a=document.querySelector("article.Sans").getBoundingClientRect(),b=document.querySelector("article.Serif").getBoundingClientRect();if(Math.abs(a.top-b.top)>1||b.left<=a.left)throw Error("parallel columns");for(const e of document.querySelectorAll(".specimen")){if(e.scrollWidth>e.clientWidth+1)throw Error("specimen overflow")}return "passed"})()'
 Call-CDP 'Emulation.setDeviceMetricsOverride' @{width=1450;height=1550;deviceScaleFactor=1;mobile=$false}|Out-Null
'''
    template = template[:a]+checks+template[b:]
    try:
        (stage/'check.ps1').write_text(template,encoding='utf-8-sig')
        result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',win+'\\check.ps1'],capture_output=True,text=True,timeout=150)
        if result.returncode:
            clean = re.sub(r'/home/[^/\s]+','~',result.stdout+result.stderr)
            clean = re.sub(r'(?i)[A-Z]:[\\/]Users[\\/][^\\/\s]+','~',clean)
            (OUT/'browser-error.txt').write_text(clean)
            raise RuntimeError('Browser verification failed; inspect build/sans-weight-audit/browser-error.txt')
        remaining(win)
        shutil.copyfile(stage/'proof.png',OUT/'browser-proof.png')
        report = json.loads((stage/'report.json').read_text(encoding='utf-8-sig'))
        (OUT/'browser-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
    finally:
        shutil.rmtree(stage)


if __name__=='__main__':
    check()
