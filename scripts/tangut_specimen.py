"""Write the local Tangut font specimen with source comparisons."""

import json
from fontTools.ttLib import TTFont
from tangut_sans import OUT, SERIF, STEM, VERSION, SAMPLES, target


def build():
    font = TTFont(SERIF, recalcTimestamp=False)
    repertoire = target(font)
    font.flavor = "woff2"
    font.save(OUT / "NotoSerifTangut-Reference.woff2")
    font.close()
    page = r"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GenZui Sans Tangut</title>
<style>
@font-face{font-family:Tangut;src:url('__STEM__.woff2') format('woff2');font-display:swap}
@font-face{font-family:Reference;src:url('NotoSerifTangut-Reference.woff2') format('woff2');font-display:swap}
:root{color-scheme:light dark;--bg:#f5f3ed;--panel:#fffefa;--ink:#232822;--muted:#686f65;--line:#d6dacf;--accent:#41674d;--size:76px}
@media(prefers-color-scheme:dark){:root{--bg:#161b18;--panel:#1f2621;--ink:#e7ece3;--muted:#a2afa2;--line:#3b473c;--accent:#9fc7a6}}
:root[data-theme=light]{color-scheme:light;--bg:#f5f3ed;--panel:#fffefa;--ink:#232822;--muted:#686f65;--line:#d6dacf;--accent:#41674d}
:root[data-theme=dark]{color-scheme:dark;--bg:#161b18;--panel:#1f2621;--ink:#e7ece3;--muted:#a2afa2;--line:#3b473c;--accent:#9fc7a6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:40px 28px 70px}
a{color:var(--accent);text-underline-offset:3px}button,input,textarea{font:inherit;color:inherit}button{cursor:pointer;background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:7px 14px}button:hover,button[aria-pressed=true]{border-color:var(--accent);color:var(--accent)}button:disabled{opacity:.4;cursor:default}input[type=search]{min-width:160px;max-width:100%;border:1px solid var(--line);background:var(--panel);border-radius:6px;padding:7px 10px}input[type=range]{accent-color:var(--accent);max-width:160px}input:focus-visible,button:focus-visible,textarea:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.brand{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;letter-spacing:.12em}.brand button{font-size:12px;letter-spacing:0}h1{font-size:clamp(32px,5vw,54px);line-height:1.12;font-weight:550;letter-spacing:-.035em;margin:35px 0 13px}.sub{color:var(--muted);margin:0}.hero{font:clamp(64px,10vw,118px)/1.6 Tangut;margin:16px 0 24px;overflow-wrap:anywhere}.downloads{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0 34px}.downloads a{padding:8px 14px;background:var(--panel);border:1px solid var(--line);border-radius:6px;text-decoration:none}.notice{max-width:740px;color:var(--muted);font-size:13px}.toolbar{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:26px;margin:30px 0 14px}.tabs,.settings{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.settings{margin:14px 0 22px;color:var(--muted);font-size:13px;gap:20px}.settings label{display:flex;align-items:center;gap:8px}
.head,.row{display:grid;grid-template-columns:115px 1fr 1fr;gap:20px;align-items:center}.head{font-size:12px;color:var(--muted);padding:12px 18px;border-bottom:1px solid var(--line)}.row{padding:18px;background:var(--panel);border-bottom:1px solid var(--line);min-width:0}.code{font:12px/1.5 ui-monospace,monospace;color:var(--muted)}.glyph{font:var(--size)/1.45 Tangut;text-align:center;min-width:0}.source{font-family:Reference}.row:first-child{border-radius:8px 8px 0 0}.row:last-child{border-radius:0 0 8px 8px}.no-source .source{display:none}.no-source .head,.no-source .row{grid-template-columns:115px 1fr}.pager{display:flex;justify-content:space-between;align-items:center;margin:20px 0;color:var(--muted);font-size:13px}.pager div{display:flex;gap:8px}h2{font-size:20px;font-weight:550;margin-top:38px}textarea{width:100%;border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:18px;font:48px/1.6 Tangut;resize:vertical;min-height:120px}footer{margin-top:38px;color:var(--muted);font-size:13px}footer p{max-width:850px}details{margin:16px 0}summary{cursor:pointer}ul{padding-left:22px}.empty{padding:40px;text-align:center;color:var(--muted)}
@media(max-width:620px){main{padding:24px 14px 48px}.head,.row{grid-template-columns:75px 1fr 1fr;gap:8px}.row{padding:12px 8px}.head{padding:10px 8px;font-size:11px}.code{font-size:10px}.glyph{font-size:min(var(--size),72px)}.no-source .head,.no-source .row{grid-template-columns:75px 1fr}.toolbar{align-items:stretch}.tabs button{padding:6px 10px;font-size:12px}.hero{font-size:65px}.settings{gap:10px}}
</style>
<main><div class="brand"><span>源萃 · TANGUT</span><button id="theme" type="button">Change theme</button></div>
<header><h1>GenZui Sans Tangut</h1><p class="sub">Regular · Version __VERSION__ · Square Gothic</p>
<div class="hero" lang="txg">𗀀𗐃𗟕𗷖𘴅</div>
<p>6,145 ideographs · 768 components · Tangut iteration mark</p>
<div class="downloads"><a href="__STEM__.ttf" download>Download TTF</a><a href="__STEM__.woff2" download>Download WOFF2</a><a href="GenZuiSansTangut-__VERSION__.zip" download>Complete package</a></div>
<p class="notice">Development version. The outlines use Noto Serif Tangut’s structures with sans strokes. Dense joins and small counters need further proofreading. Coverage follows the source font; later Tangut additions and Components Supplement are absent.</p></header>
<div class="toolbar"><div class="tabs" aria-label="Character groups"><button data-group="complex" aria-pressed="true">Examples</button><button data-group="components" aria-pressed="false">Components</button><button data-group="all" aria-pressed="false">All characters</button></div><input id="search" type="search" aria-label="Find a character or code point" placeholder="Character or U+17000"></div>
<div class="settings"><label>Size <input id="size" type="range" min="32" max="128" value="76"><output id="size-value">76 px</output></label><label><input id="compare" type="checkbox" checked>Compare serif source</label></div>
<section id="comparison" aria-label="Font comparison"><div class="head"><span>Character</span><span class="source" style="font-family:inherit">Noto Serif Tangut</span><span>GenZui Sans Tangut</span></div><div id="rows"></div></section>
<div class="pager"><span id="position" aria-live="polite"></span><div><button id="previous">Previous</button><button id="next">Next</button></div></div>
<h2>Try the font</h2><textarea aria-label="Tangut sample text" lang="txg">𗀀𗐃𗟕𗷖𘴅𘠀𘠁𘠂𘢌</textarea>
<footer><p>Install the TTF as <strong>GenZui Sans Tangut</strong>. For web text, load <a href="genzui-sans-tangut.css">the stylesheet</a> and include this family beside GenZui Sans. This face contains Tangut, spaces and the iteration mark.</p>
<details open><summary>Sources and licences</summary><ul><li><a href="https://github.com/notofonts/noto-fonts/tree/526169d273a5d9b22035d72ec509932fb7abd59a/unhinted/ttf/NotoSerifTangut">Noto Serif Tangut 2.168</a>: character structure and repertoire.</li><li><a href="https://github.com/notofonts/noto-cjk/tree/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Sans">Noto Sans CJK JP Regular 2.004</a>: stroke outlines.</li><li><a href="https://github.com/mkpoli/GenZui">GenZui</a>: stroke reconstruction, fitting and spacing.</li></ul><p><a href="OFL.txt">SIL Open Font License 1.1</a> · <a href="NOTICE.txt">Credits</a> · <a href="sources.json">Source hashes and character records</a> · <a href="checks.json">Font validation</a></p></details></footer>
</main>
<script>
const cps=__REPERTOIRE__, samples=__SAMPLES__, pageSize=48;
let group='complex', page=0;
const rows=document.querySelector('#rows'), search=document.querySelector('#search');
function render(){
 const query=search.value.trim();let chosen=group==='complex'?samples.filter(cp=>cp<0x18800||cp>=0x18d00):group==='components'?cps.filter(cp=>cp>=0x18800&&cp<=0x18aff):cps;
 if(query){const hex=/^(?:U\+|0x)([0-9a-f]+)$/i.exec(query);const wanted=hex?[parseInt(hex[1],16)]:Array.from(query,c=>c.codePointAt(0));chosen=cps.filter(cp=>wanted.includes(cp));}
 const pages=Math.max(1,Math.ceil(chosen.length/pageSize));page=Math.min(page,pages-1);rows.replaceChildren();
 for(const cp of chosen.slice(page*pageSize,(page+1)*pageSize)){
  const row=document.createElement('div');row.className='row';row.dataset.codepoint=cp.toString(16).toUpperCase();
  const code=document.createElement('span');code.className='code';code.textContent='U+'+cp.toString(16).toUpperCase();row.append(code);
  for(const cls of ['glyph source','glyph result']){const cell=document.createElement('span');cell.className=cls;cell.lang='txg';cell.textContent=String.fromCodePoint(cp);row.append(cell)}rows.append(row);
 }
 if(!chosen.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='No matching character in this font.';rows.append(empty)}
 document.querySelector('#position').textContent=chosen.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,chosen.length)} of ${chosen.length.toLocaleString()}`:'0 characters';
 document.querySelector('#previous').disabled=page===0;document.querySelector('#next').disabled=page===pages-1;
}
for(const tab of document.querySelectorAll('[data-group]'))tab.addEventListener('click',()=>{group=tab.dataset.group;page=0;search.value='';for(const b of document.querySelectorAll('[data-group]'))b.setAttribute('aria-pressed',String(b===tab));render()});
search.addEventListener('input',()=>{page=0;render()});
document.querySelector('#previous').addEventListener('click',()=>{page--;render()});document.querySelector('#next').addEventListener('click',()=>{page++;render()});
document.querySelector('#size').addEventListener('input',e=>{document.documentElement.style.setProperty('--size',e.target.value+'px');document.querySelector('#size-value').textContent=e.target.value+' px'});
document.querySelector('#compare').addEventListener('change',e=>document.querySelector('#comparison').classList.toggle('no-source',!e.target.checked));
document.querySelector('#theme').addEventListener('click',()=>{const dark=document.documentElement.dataset.theme?document.documentElement.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;document.documentElement.dataset.theme=dark?'light':'dark'});
render();
</script></html>"""
    page = page.replace("__REPERTOIRE__", json.dumps(repertoire)).replace(
        "__SAMPLES__", json.dumps(SAMPLES)
    )
    page = page.replace("__STEM__", STEM).replace("__VERSION__", VERSION)
    (OUT / "index.html").write_text(page)
    print("Wrote build/tangut-sans/index.html")


if __name__ == "__main__":
    build()
