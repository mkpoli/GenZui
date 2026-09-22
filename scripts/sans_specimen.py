"""Offline specimen and contact sheet for GenZui Sans."""
import base64
from PIL import Image, ImageDraw, ImageFont

from repertoire import repertoire


def build_specimen():
    from sans import OUT, STEM, VERSION
    webfont = base64.b64encode((OUT/(STEM+'.woff2')).read_bytes()).decode()
    groups = [
        ('Hentaigana', ''.join(chr(cp) for cp in range(0x1B001, 0x1B11F))),
        ('Historical kana', ''.join(item['character'] for item in repertoire()
                                    if item['group'] in ('historic-kana', 'small-kana', 'cjk-kana-ligature'))),
        ('Minnan kana', 'チウ̅チア𚿰 チゥ̣チァム𚿵 ウ̣̅ オ̣̅'),
        ('Transcription symbols', '卄𝍲𝍳𝍴𝍵𝍶⿼⿽⿾⿿㇯'),
    ]
    sections = ''.join(f'<section><h2>{title}</h2><p class="glyphs" lang="ja">{text}</p></section>'
                       for title, text in groups)
    source = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GenZui Sans — 源萃ゴシック</title><style>
@font-face{font-family:GenZui;src:url(data:font/woff2;base64,FONT) format('woff2');font-weight:400;font-display:swap}
:root{color:#202921;background:#f4f3ed;font:16px/1.6 system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0}main{max-width:1160px;margin:auto;padding:56px 32px}
header{border-bottom:1px solid #bfc6b9;padding-bottom:28px}h1{font:clamp(42px,6vw,72px)/1.25 GenZui;margin:12px 0 22px;letter-spacing:-.025em}
.kicker{font-size:13px;letter-spacing:.13em;text-transform:uppercase;color:#48604d}p{max-width:850px}
a{color:#325e43;text-underline-offset:3px}.links{display:flex;gap:24px;flex-wrap:wrap}
h2{font-size:18px;font-weight:600;margin:0 0 20px}section{padding:32px 0;border-bottom:1px solid #c9cec3}
.controls{display:flex;gap:24px;flex-wrap:wrap;align-items:center;font-size:14px;margin:22px 0}
label{display:flex;align-items:center;gap:8px}input{accent-color:#365a41}button{font:inherit;padding:7px 13px;border:1px solid #acb5a7;background:#fafaf6;border-radius:4px;color:inherit;cursor:pointer}
.sample{font:var(--size,44px)/1.8 GenZui;min-height:200px;padding:20px;background:#fffefa;border:1px solid #bfc6b9;white-space:pre-wrap;overflow:auto}
.sample.vertical{writing-mode:vertical-rl;height:460px;width:100%;white-space:normal}
.glyphs{font:36px/2 GenZui;max-width:none;overflow-wrap:anywhere;letter-spacing:.08em}
footer{font-size:14px;padding-top:30px;color:#586250}code{font-size:.9em}.small{font-size:14px;color:#586250}
@media(max-width:600px){main{padding:28px 18px}.glyphs{font-size:28px}.sample{--size:32px}}
</style><main><header><div class="kicker">Regular · VERSION</div><h1 lang="ja">源萃ゴシック<br>GenZui Sans</h1>
<p>A Japanese sans-serif for modern text and historical kana, with all 286 hentaigana, the Unicode 18 kana additions and Minnan tone letters.</p>
<nav class="links"><a href="GenZuiSans-Regular.ttf" download>Download TTF</a><a href="GenZuiSans-Regular.woff2" download>Download WOFF2</a><a href="OFL.txt">SIL Open Font License</a></nav></header>
<section><h2>Try the font</h2><div class="controls"><label>Size <input id="size" type="range" min="20" max="88" value="44"><output id="size-value">44 px</output></label><button id="direction" type="button" aria-pressed="false">Vertical text</button><label><input id="hooked" type="checkbox">Hooked WU</label></div>
<div class="sample" id="sample" contenteditable="true" role="textbox" aria-label="Font specimen text" aria-multiline="true" lang="ja" spellcheck="false">いろはにほへと ちりぬるを
あいうえお　𛀂𛀆𛀋𛀁𛀔
𛄟𛄣 𛄤𛄥𛄦 𛄧𛄨𛅨
日本語の文字と、むかしの仮名。</div>
<p class="small">Edit the text above. Hooked WU uses <code>ss01</code>.</p></section>
SECTIONS
<footer><p>Based on Noto Sans JP and Noto Sans Hentaigana, with historical forms from GenSeki Hentaigana Gothic, Minnan signs from FRB Taiwanese Kana, and GenZui drawings. <a href="NOTICE.txt">Source credits</a> · <a href="checks.json">Font checks</a></p></footer></main>
<script>const sample=document.getElementById('sample');document.getElementById('size').addEventListener('input',e=>{sample.style.setProperty('--size',e.target.value+'px');document.getElementById('size-value').textContent=e.target.value+' px'});document.getElementById('direction').addEventListener('click',e=>{const vertical=sample.classList.toggle('vertical');e.currentTarget.setAttribute('aria-pressed',String(vertical));e.currentTarget.textContent=vertical?'Horizontal text':'Vertical text'});document.getElementById('hooked').addEventListener('change',e=>{sample.style.fontFeatureSettings=e.target.checked?'"ss01" 1':'normal'});</script></html>'''
    (OUT/'index.html').write_text(source.replace('FONT', webfont).replace('VERSION', VERSION).replace('SECTIONS', sections))
    (OUT/'genzui-sans.css').write_text(
        "@font-face {\n  font-family: 'GenZui Sans';\n  src: url('GenZuiSans-Regular.woff2') format('woff2');\n"
        "  font-weight: 400;\n  font-style: normal;\n  font-display: swap;\n}\n")

    face = ImageFont.truetype(str(OUT/(STEM+'.ttf')), 58)
    small = ImageFont.truetype(str(OUT/(STEM+'.ttf')), 17)
    title_face = ImageFont.truetype(str(OUT/(STEM+'.ttf')), 36)
    samples = [('Modern kana', 'あいうえおかきくけこさしすせそ'),
               ('Hentaigana', '𛀂𛀃𛀆𛀋𛀗𛀲𛀼𛁄𛁒𛁩𛂒𛂰𛃂𛃱𛄍'),
               ('Historical kana', '𛄟𛄣𛄤𛄥𛄦𛄧𛄨𛅨𪜈𬻿𬼀𬼂'),
               ('Small kana', ''.join(ch+chr(cp) for ch, cp in [('こ', 0x1B132), ('ゐ', 0x1B150), ('ゑ', 0x1B151), ('を', 0x1B152), ('コ', 0x1B155), ('ヰ', 0x1B164), ('ヱ', 0x1B165), ('ヲ', 0x1B166)])),
               ('Minnan and transcription', 'チア𚿰 チウ̅ チゥ̣ 卄𝍲𝍳𝍴𝍵𝍶⿼⿽⿾⿿㇯'),
               ('Japanese text', '日本語の文字と、むかしの仮名。')]
    image = Image.new('RGB', (1440, 100+len(samples)*136), '#f4f3ed')
    draw = ImageDraw.Draw(image)
    draw.text((48, 25), '源萃ゴシック  GenZui Sans Regular', font=title_face, fill='#233d2c')
    for row, (label, text) in enumerate(samples):
        y = 103+row*136
        draw.text((48, y), label, font=small, fill='#586250')
        draw.text((48, y+27), text, font=face, fill='#202921')
        draw.line((48, y+115, 1392, y+115), fill='#c9cec3')
    image.save(OUT/'preview.png')

    # Every hentaigana has a labelled cell for inspection.
    points = list(range(0x1B001, 0x1B11F))
    sheet = Image.new('RGB', (1440, ((len(points)+11)//12)*126), 'white')
    pen = ImageDraw.Draw(sheet)
    for i, cp in enumerate(points):
        x, y = (i%12)*120, (i//12)*126
        pen.text((x+26, y+8), chr(cp), font=face, fill='#202921')
        pen.text((x+16, y+85), f'U+{cp:05X}', font=small, fill='#586250')
    sheet.save(OUT/'hentaigana-contact-sheet.png')


if __name__ == '__main__':
    build_specimen()
