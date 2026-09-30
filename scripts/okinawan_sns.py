"""Render sentence specimens from the actual release fonts, in GenZui colours."""
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
SOURCE_URL = 'https://manoa.hawaii.edu/okinawa/handbook_l3_proverbs.pdf'
INK, GREEN, MUTED, PAPER = '#25382e', '#214e3c', '#63776a', '#f7f8f2'
SENTENCES = [
    {'text': 'ぬちどぅ たから。', 'meaning': '命こそ宝。'},
    {'text': 'うや ゆし、くゎ ゆし。', 'meaning': '親が教え、子が教える。'},
    {'text': 'あわてぃーる なーか うてぃちき。', 'meaning': '慌てるときこそ、落ち着いて。'},
]

CHARACTER_LABELS = ('TU', 'DU', 'TI', 'DI', 'KWA', 'GWA',
                    'KWI', 'GWI', 'KWE', 'GWE', 'HWA', 'HWI',
                    'HWE', 'WU', 'SI', 'ZI', 'TSI', 'DZI')
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
    def canvas():
        image = Image.new('RGB', (2400, 2400), PAPER)
        return image, ImageDraw.Draw(image)
    def text(draw, x, y, value, size, style='Regular', colour=INK, latin=False):
        face = 'DejaVuSans.ttf' if latin else str(fonts[style])
        font = ImageFont.truetype(face, round(size*2), layout_engine=ImageFont.Layout.RAQM)
        value = compose(value)
        assert draw.textlength(value, font=font) <= (1200-x-60)*2, value
        draw.text((x*2, y*2), value, font=font, fill=colour, anchor='ls')
    def footer(draw, n, source=True):
        draw.line((144, 2140, 2256, 2140), fill='#cdd7cb', width=2)
        text(draw, 72, 1116, 'genzui.mkpo.li/serif', 22, colour=GREEN, latin=True)
        text(draw, 830, 1116, f'{VERSION}  /  {n:02d}', 20, colour=MUTED, latin=True)
        if source:
            text(draw, 72, 1160, '出典：ハワイ大学「ことわざ」　合字による表記', 19, colour=MUTED)
        else:
            text(draw, 72, 1160, '船津式沖縄語仮名より', 19, colour=MUTED)
    cards = []
    for style in ('Regular', 'Bold'):
        image, draw = canvas()
        text(draw, 72, 76, 'GENZUI SERIF', 22, colour=GREEN, latin=True)
        text(draw, 72, 184, '源萃明朝', 76)
        text(draw, 750, 179, '沖縄語の仮名', 26, colour=MUTED)
        draw.rectangle((0, 470, 2400, 594), fill=GREEN)
        text(draw, 72, 277, style.upper(), 22, colour=PAPER, latin=True)
        text(draw, 855, 277, '合字と濁音', 24, colour=PAPER)
        glyph_font = ImageFont.truetype(str(fonts[style]), 244, layout_engine=ImageFont.Layout.RAQM)
        label_font = ImageFont.truetype('DejaVuSans.ttf', 38)
        for i, item in enumerate(CHARACTERS):
            col, row = i % 6, i // 6
            centre, baseline = 160 + col*176, 486 + row*247
            bounds = draw.textbbox((centre*2, baseline*2), item['text'], font=glyph_font, anchor='ms')
            assert bounds[0] >= (centre-88)*2 and bounds[2] <= (centre+88)*2, item['label']
            assert bounds[1] >= (baseline-180)*2 and bounds[3] < (baseline+45)*2, item['label']
            draw.text((centre*2, baseline*2), item['text'], font=glyph_font, fill=INK, anchor='ms')
            draw.text((centre*2, (baseline+58)*2), item['label'], font=label_font, fill=MUTED, anchor='ms')
        footer(draw, 1 if style == 'Regular' else 2, source=False)
        name = f'genzui-{VERSION}-okinawan-characters-{style.lower()}.png'
        image.save(OUT/name, optimize=True)
        cards.append((name, f'源萃明朝の{style}による沖縄語の仮名18字。' + '、'.join(CHARACTER_LABELS) + '。'))
    image, draw = canvas()
    text(draw, 72, 76, 'GENZUI SERIF', 22, colour=GREEN, latin=True)
    text(draw, 72, 184, '源萃明朝', 76)
    text(draw, 750, 179, '沖縄語の組見本', 26, colour=MUTED)
    draw.rectangle((0, 500, 2400, 1300), fill=GREEN)
    text(draw, 72, 325, 'REGULAR', 18, colour='#bdd1c0', latin=True)
    text(draw, 72, 500, 'ぬちどぅ たから。', 125, colour=PAPER)
    text(draw, 76, 588, '命こそ宝。', 31, colour='#bdd1c0')
    text(draw, 72, 739, 'BOLD', 18, colour=MUTED, latin=True)
    text(draw, 72, 865, 'うや ゆし、くゎ ゆし。', 80, 'Bold')
    text(draw, 76, 948, '親が教え、子が教える。', 30, colour=MUTED)
    footer(draw, 3)
    image.save(OUT/'genzui-0.118-okinawan-sentences.png', optimize=True)
    image, draw = canvas()
    text(draw, 72, 76, 'GENZUI SERIF', 22, colour=GREEN, latin=True)
    text(draw, 72, 175, '沖縄のことわざ', 65)
    text(draw, 76, 246, SENTENCES[2]['meaning'], 28, colour=MUTED)
    for style, top in [('Regular', 327), ('Bold', 694)]:
        text(draw, 72, top, style.upper(), 18, colour=MUTED, latin=True)
        text(draw, 72, top+117, 'あわてぃーる なーか', 85, style)
        text(draw, 72, top+242, 'うてぃちき。', 85, style)
    footer(draw, 4)
    image.save(OUT/'genzui-0.118-okinawan-weights.png', optimize=True)
    for lang in ('ja', 'en'):
        shutil.copyfile(ROOT/'release'/f'announcement-{VERSION}-{lang}.txt', OUT/f'announcement-{lang}.txt')
    manifest = {'version': VERSION, 'source': SOURCE_URL, 'pages': ['3-2', '3-3'],
                'sentences': SENTENCES, 'characters': [{'label': e['label'], 'text': e['text'], 'codepoints': e['output']} for e in CHARACTERS], 'font_sha256': {s: hashlib.sha256(p.read_bytes()).hexdigest() for s, p in fonts.items()},
                'size': [2400, 2400], 'colour_mode': 'RGB',
                'note': 'Traditional proverbs. Punctuation and line breaks are editorial; kana digraphs are set as GenZui ligatures.'}
    cards += [('genzui-0.118-okinawan-sentences.png', '沖縄のことわざ。「ぬちどぅ たから。」をRegular、「うや ゆし、くゎ ゆし。」をBoldで組んだ源萃明朝の見本。'),
             ('genzui-0.118-okinawan-weights.png', '「あわてぃーる なーか うてぃちき。」を源萃明朝のRegularとBoldで比較した組見本。')]
    manifest['images'] = [{'file': name, 'alt_ja': alt, 'sha256': hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name, alt in cards]
    (OUT/'specimens.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (OUT/'alt-ja.txt').write_text('\n\n'.join(n+'\n'+alt for n, alt in cards)+'\n')
    page = '''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>源萃明朝 · SNS</title><style>*{box-sizing:border-box}body{margin:0;background:#f7f8f2;color:#25382e;font:16px/1.7 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:30px}a{color:#214e3c}.images{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0}img{width:100%;display:block}textarea{width:100%;min-height:220px;padding:16px;font:inherit;background:white;border:1px solid #cdd7cb}button{padding:8px 16px;font:inherit;background:#214e3c;color:white;border:0;cursor:pointer}p{color:#63776a}h1{font-size:28px}@media(max-width:700px){.images{grid-template-columns:1fr}main{padding:18px}}</style><main><a href="../">字形比較に戻る</a><h1>源萃明朝0.118 · SNS</h1><p>字形一覧2枚と、ことわざの組見本2枚。PNGは2400×2400px。</p><div class="images">'''
    for name, alt in cards:
        page += f'<figure><a href="{name}"><img src="{name}" alt="{html.escape(alt)}"></a><figcaption><a href="{name}" download>PNGを保存</a></figcaption></figure>'
    page += '</div>'
    for lang, label in [('ja', '日本語'), ('en', 'English')]:
        copy = (OUT/f'announcement-{lang}.txt').read_text()
        page += f'<h2>{label}</h2><textarea id="{lang}">{html.escape(copy)}</textarea><button data-copy="{lang}">Copy</button>'
    page += f'<p>ことわざの出典：<a href="{SOURCE_URL}">ハワイ大学「ことわざ」</a>、3-2・3-3頁。句読点と改行を整え、「とぅ・てぃ・くゎ」を合字で表記。</p><p><a href="alt-ja.txt">画像の代替テキスト</a></p><span id="status" role="status"></span></main><script>document.querySelectorAll("[data-copy]").forEach(b=>b.onclick=async()=>{{const t=document.getElementById(b.dataset.copy);try{{await navigator.clipboard.writeText(t.value);document.getElementById("status").textContent="Copied."}}catch{{t.focus();t.select();document.getElementById("status").textContent="Select and copy the text."}}}})</script></html>'
    (OUT/'index.html').write_text(page)
    print('SNS: four 2400px images (characters and sentences), JA/EN copy, alt text and source record.')


if __name__ == '__main__':
    build()
