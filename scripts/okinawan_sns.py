"""Render one character and sentence specimen from the approved release fonts."""
import hashlib
import html
import json
import shutil

from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont

from sources import ROOT
from serif import OUT as FONT_OUT, VERSION
from okinawan_release_proof import OUT as PROOF_OUT
from okinawan import ENTRIES

OUT = PROOF_OUT / 'sns'
CHARACTER_SOURCE_URL = 'https://github.com/ctrlcctrlv/OkinawanKanaUnicodePaper/blob/main/okana.pdf'
SOURCE_URL = 'https://manoa.hawaii.edu/okinawa/handbook_l3_proverbs.pdf'
INK, GREEN, MUTED, PAPER = '#25382e', '#214e3c', '#63776a', '#f7f8f2'
SENTENCES = [
    {'text': 'あわてぃーる なーか うてぃちき。', 'meaning': '慌てるときこそ、落ち着いて。'},
]

CHARACTER_LABELS = ('TU', 'DU', 'TI', 'DI', 'KWA', 'GWA', 'KWI', 'GWI', 'KWE',
                    'GWE', 'HWA', 'HWI', 'HWE', 'Glottal YA', 'Glottal YU',
                    'Glottal YO', 'Glottal WA', 'Glottal WI', 'Glottal WE',
                    'Glottal N', 'YI', 'YE', 'WU', 'SI', 'ZI', 'TSI', 'DZI')
ENTRIES_BY_LABEL = {e['label']: e for e in ENTRIES}
CHARACTERS = [{'label': label, 'output': ENTRIES_BY_LABEL[label]['output'],
               'text': ''.join(chr(int(cp, 16)) for cp in ENTRIES_BY_LABEL[label]['output'])}
              for label in CHARACTER_LABELS]


def compose(value):
    for a, b in [('どぅ', '\uf450\u3099'), ('とぅ', '\uf450'),
                 ('てぃ', '\uf452'), ('くゎ', '\uf454')]:
        value = value.replace(a, b)
    return value


def build():
    assert features.check('raqm'), 'Sentence rendering needs HarfBuzz/RAQM shaping.'
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = {style: FONT_OUT / f'GenZuiSerif-{style}.ttf' for style in ('Regular', 'Bold')}
    for style, path in fonts.items():
        cmap = TTFont(path).getBestCmap()
        for sample in SENTENCES + CHARACTERS:
            assert set(map(ord, compose(sample['text']))) <= set(cmap)
    scale = 2
    width, height = 1200, 630
    field, panel, ivory = '#06241a', '#0b3326', '#f4f7f1'
    green, mint, accent = '#1f634d', '#86b09a', '#3fae84'
    image = Image.new('RGB', (width*scale, height*scale), field)
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 32):
        draw.line((x*scale, 0, x*scale, height*scale), fill='#0a2d21', width=scale)
    for y in range(0, height, 32):
        draw.line((0, y*scale, width*scale, y*scale), fill='#0a2d21', width=scale)

    def text(x, y, value, size, style='Regular', colour=ivory, latin=False, anchor='ls'):
        face = 'DejaVuSans.ttf' if latin else str(fonts[style])
        font = ImageFont.truetype(face, round(size*scale), layout_engine=ImageFont.Layout.RAQM)
        value = compose(value)
        bounds = draw.textbbox((x*scale, y*scale), value, font=font, anchor=anchor)
        assert 0 <= bounds[0] < bounds[2] <= width*scale and 0 <= bounds[1] < bounds[3] <= height*scale, value
        draw.text((x*scale, y*scale), value, font=font, fill=colour, anchor=anchor)

    def brackets(x0, y0, x1, y1):
        for x, y, dx, dy in ((x0,y0,1,1),(x1,y0,-1,1),(x0,y1,1,-1),(x1,y1,-1,-1)):
            draw.line((x*scale,y*scale,(x+16*dx)*scale,y*scale),fill=accent,width=scale*2)
            draw.line((x*scale,y*scale,x*scale,(y+16*dy)*scale),fill=accent,width=scale*2)

    text(60, 63, '源萃明朝', 34, 'Bold')
    text(1140, 60, VERSION, 14, colour=mint, latin=True, anchor='rs')
    top, bottom, panel_width = 96, 570, 525
    for style, left, fill, ink, muted in [
            ('Regular', 60, ivory, green, '#5f7d6e'),
            ('Bold', 615, panel, ivory, mint)]:
        right = left + panel_width
        draw.rectangle((left*scale,top*scale,right*scale,bottom*scale),fill=fill,
                       outline=green if style=='Bold' else None,width=scale)
        brackets(left-6,top-6,right+6,bottom+6)
        text(left+28, top+32, style.upper(), 12, colour=muted, latin=True)
        for i, item in enumerate(CHARACTERS):
            col, row = i % 9, i // 9
            text(left+44+col*54.5, top+108+row*85, item['text'], 43, style, ink, anchor='ms')
        draw.line(((left+28)*scale,405*scale,(right-28)*scale,405*scale),
                  fill='#cbd8cb' if style=='Regular' else green,width=scale)
        lines = ('あわてぃーる なーか', 'うてぃちき。')
        for row, line in enumerate(lines):
            text(left+36,475+row*59,line,38,style,ink)
    text(60, 610, 'genzui.mkpo.li', 16, colour=mint, latin=True)
    name = f'genzui-{VERSION}-okinawan.png'
    image.save(OUT/name, optimize=True)
    # Replace the former four-image set with the single composition.
    for suffix in ('characters-regular', 'characters-bold', 'sentences', 'weights'):
        (OUT/f'genzui-{VERSION}-okinawan-{suffix}.png').unlink(missing_ok=True)
    cards = [(name, '源萃明朝の新沖縄文字27字をRegularとBoldで比較。左がRegular、右がBold。それぞれの下に「あわてぃーる なーか うてぃちき。」を組んだ見本。')]
    for lang in ('ja', 'en'):
        shutil.copyfile(ROOT/'release'/f'announcement-{VERSION}-{lang}.txt', OUT/f'announcement-{lang}.txt')
    manifest = {'version': VERSION, 'source': SOURCE_URL, 'character_source': CHARACTER_SOURCE_URL, 'pages': ['3-2'],
                'sentences': SENTENCES, 'characters': [{'label': e['label'], 'text': e['text'], 'codepoints': e['output']} for e in CHARACTERS], 'font_sha256': {s: hashlib.sha256(p.read_bytes()).hexdigest() for s, p in fonts.items()},
                'size': [2400, 1260], 'colour_mode': 'RGB',
                'note': 'Traditional proverbs. Punctuation and line breaks are editorial; kana digraphs are set as GenZui ligatures.'}
    manifest['images'] = [{'file': name, 'alt_ja': alt, 'sha256': hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name, alt in cards]
    (OUT/'specimens.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (OUT/'alt-ja.txt').write_text('\n\n'.join(n+'\n'+alt for n, alt in cards)+'\n')
    page = '''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>源萃明朝 · SNS</title><style>*{box-sizing:border-box}body{margin:0;background:#f7f8f2;color:#25382e;font:16px/1.7 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:30px}a{color:#214e3c}.images{max-width:960px}figure{margin:0}img{width:100%;display:block}textarea{width:100%;min-height:220px;padding:16px;font:inherit;background:white;border:1px solid #cdd7cb}button{padding:8px 16px;font:inherit;background:#214e3c;color:white;border:0;cursor:pointer}p{color:#63776a}h1{font-size:28px}@media(max-width:700px){.images{grid-template-columns:1fr}main{padding:18px}}</style><main><a href="../">字形比較に戻る</a><h1>源萃明朝0.118 · SNS</h1><p>PNG・2400×1260px。</p><div class="images">'''
    for name, alt in cards:
        page += f'<figure><a href="{name}"><img src="{name}" alt="{html.escape(alt)}"></a><figcaption><a href="{name}" download>PNGを保存</a></figcaption></figure>'
    page += '</div>'
    for lang, label in [('ja', '日本語'), ('en', 'English')]:
        copy = (OUT/f'announcement-{lang}.txt').read_text()
        page += f'<h2>{label}</h2><textarea id="{lang}">{html.escape(copy)}</textarea><button data-copy="{lang}">Copy</button>'
    page += f'<p>ことわざの出典：<a href="{SOURCE_URL}">ハワイ大学「ことわざ」</a>、3-2頁。句読点と改行を整え、「てぃ」を合字で表記。</p><p>文字の由来：<a href="{CHARACTER_SOURCE_URL}">新沖縄文字の符号化提案</a></p><p><a href="alt-ja.txt">画像の代替テキスト</a></p><span id="status" role="status"></span></main><script>document.querySelectorAll("[data-copy]").forEach(b=>b.onclick=async()=>{{const t=document.getElementById(b.dataset.copy);try{{await navigator.clipboard.writeText(t.value);document.getElementById("status").textContent="Copied."}}catch{{t.focus();t.select();document.getElementById("status").textContent="Select and copy the text."}}}})</script></html>'
    (OUT/'index.html').write_text(page)
    print('SNS: one 2400px character and sentence image, JA/EN copy, alt text and source record.')


if __name__ == '__main__':
    build()
