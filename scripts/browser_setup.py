"""Build a local installer guide and browser fallback preview."""
import html
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/browser'
OUT.mkdir(parents=True, exist_ok=True)
script = ROOT / 'browser/historical-kana-fallback.user.js'
samples = [
    ('Hentaigana', ''.join(chr(cp) for cp in [0x1B001, 0x1B002, 0x1B003, 0x1B006, 0x1B00B, 0x1B052, 0x1B08B])),
    ('Unicode 18', ''.join(chr(cp) for cp in [*range(0x1B123, 0x1B129), 0x1B168])),
    ('Combining marks', chr(0x1B002) + '\u3099 ' + chr(0x1B0A9) + '\u309a'),
    ('Mixed text', 'ABC かな漢字 ' + chr(0x1B002) + chr(0x1B123)),
]
rows = ''.join('<tr><th>' + label + '</th><td class="auto">' + text +
               '</td><td class="reference">' + text + '</td></tr>' for label, text in samples)
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Historical kana browser setup</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f4ee;color:#252e28;font:16px/1.6 system-ui,sans-serif}main{max-width:1180px;padding:36px;margin:auto}h1{font-size:30px;line-height:1.25}h2{font-size:21px;margin-top:32px}a{color:#176953}button{background:#215c49;color:white;border:0;border-radius:5px;padding:11px 18px;font:inherit;cursor:pointer}button:disabled{background:#62776c}textarea{width:100%;height:260px;font:13px/1.5 Consolas,monospace;padding:15px;background:white;border:1px solid #bbb}table{border-collapse:collapse;width:100%;background:white}th,td{border:1px solid #cbd0c6;padding:12px;text-align:center}th{font-size:14px}td{font-size:36px;line-height:1.6}.auto{font-family:Arial}.reference{font-family:"GenSeki Hentaigana Gothic"}.scroll{overflow-x:auto}code{font-size:.92em}.note{background:#e8eee6;padding:14px;border-left:3px solid #527a5f}#copy-status{margin-left:10px}details{margin-top:20px}
</style><main><h1>Historical kana browser setup</h1>
<p>Use <a href="https://github.com/MihailJP/GenSekiHentaiganaGothic/releases">GenSeki Hentaigana Gothic</a> Regular and Bold for historical kana, including the seven additions in Unicode 18. The font must be installed in Windows.</p>
<h2>Chrome and Vivaldi</h2>
<ol><li>Install <a href="https://www.tampermonkey.net/index.php?browser=chrome">Tampermonkey</a> if it is not already installed.</li><li>Open Tampermonkey → <strong>Create a new script</strong>.</li><li>Copy the script below, replace the editor's template, then press <strong>Ctrl+S</strong>.</li><li>If Tampermonkey requests permission to run scripts, enable <strong>Allow User Scripts</strong> on its extension details page. See <a href="https://www.tampermonkey.net/faq.php?locale=en&amp;q=Q209">the official instructions</a>.</li><li>Reload the affected web page.</li></ol>
<p><button id="copy">Copy userscript</button><span id="copy-status" role="status"></span></p>
<textarea id="source" readonly aria-label="Historical kana fallback userscript">SOURCE</textarea>
<p>The helper fills historical-kana gaps in a page's font stack. Other characters keep using the page's existing fonts. It runs locally and makes no network requests.</p>
<h2>Firefox</h2>
<p>Append <code>GenSeki Hentaigana Gothic</code> to the existing values of these string preferences in <code>about:config</code>. Keep existing font names and their order. Create an absent preference as a string containing the family name.</p>
<pre>font.name-list.serif.ja
font.name-list.sans-serif.ja
font.name-list.monospace.ja
font.name-list.serif.x-unicode
font.name-list.sans-serif.x-unicode
font.name-list.monospace.x-unicode</pre>
<p>Fully exit and reopen Firefox after installing fonts or configuring <code>user.js</code>.</p>
<h2>Preview on this page</h2>
<p>The left column requests Arial; the right column requests GenSeki. The button below enables the helper for this preview. This local preview does not install the userscript or check whether it is enabled on websites.</p>
<p><button id="preview">Preview kana fallback</button></p>
<div class="scroll"><table lang="ja"><thead><tr><th>Sample</th><th>Page font with fallback</th><th>GenSeki reference</th></tr></thead><tbody>ROWS</tbody></table></div>
<details><summary>All 286 hentaigana</summary><p class="auto" lang="ja" style="font-size:32px;overflow-wrap:anywhere">ALL</p></details>
<p class="note">The userscript applies to ordinary HTTP and HTTPS page text. Browser interface pages, PDF viewers, canvas text and shadow roots need their own font support.</p>
<p><a href="historical-kana-fallback.user.js">Userscript file</a> · <a href="README.md">Setup notes</a> · <a href="LICENSE.txt">Script licence</a></p>
</main><script>
document.getElementById('copy').addEventListener('click',async()=>{const source=document.getElementById('source');const status=document.getElementById('copy-status');try{await navigator.clipboard.writeText(source.value);status.textContent='Copied. Paste into the Tampermonkey editor.'}catch{source.focus();source.select();status.textContent='Press Ctrl+C to copy the selected script.'}});
document.getElementById('preview').addEventListener('click',event=>{const button=event.currentTarget;button.disabled=true;globalThis.GM_addStyle=css=>{const style=document.createElement('style');style.textContent=css;document.head.append(style);return style;};const script=document.createElement('script');script.src='historical-kana-fallback.user.js';script.onload=()=>button.textContent='Preview active';script.onerror=()=>{button.textContent='Keep the HTML and userscript in the same folder';button.disabled=false};document.body.append(script);});
</script></html>'''
page = page.replace('SOURCE', html.escape(script.read_text())).replace('ROWS', rows)
page = page.replace('ALL', ''.join(chr(cp) for cp in range(0x1B001, 0x1B11F)))
(OUT / 'browser-setup.html').write_text(page)
shutil.copy2(script, OUT / script.name)
shutil.copy2(ROOT / 'browser/README.md', OUT / 'README.md')
shutil.copy2(ROOT / 'LICENSE-scripts.txt', OUT / 'LICENSE.txt')
print('Built browser setup page and userscript.')
