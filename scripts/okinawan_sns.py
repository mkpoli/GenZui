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
SOURCE_URL = 'https://manoa.hawaii.edu/okinawa/handbook_l3_proverbs.pdf'
INK, GREEN, MUTED, PAPER = '#25382e', '#214e3c', '#63776a', '#f7f8f2'
SENTENCES = [
    {'text': 'ぬちどぅ たから。', 'meaning': '命こそ宝。'},
    {'text': 'うや ゆし、くゎ ゆし。', 'meaning': '親が教え、子が教える。'},
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
    image = Image.new('RGB', (2400, 2400), PAPER)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size, style='Regular', colour=INK, latin=False, anchor='ls'):
        face = 'DejaVuSans.ttf' if latin else str(fonts[style])
        font = ImageFont.truetype(face, round(size*2), layout_engine=ImageFont.Layout.RAQM)
        value = compose(value)
        bounds = draw.textbbox((x*2, y*2), value, font=font, anchor=anchor)
        assert 0 <= bounds[0] < bounds[2] <= 2400 and 0 <= bounds[1] < bounds[3] <= 2400, value
        draw.text((x*2, y*2), value, font=font, fill=colour, anchor=anchor)

    text(72, 140, '源萃明朝', 72)
    draw.rectangle((0, 1360, 2400, 2400), fill=GREEN)
    for style, label_y, first_y, sentence_y, colour in [
            ('Regular', 214, 342, 604, INK),
            ('Bold', 730, 850, 1115, PAPER)]:
        text(72, label_y, style.upper(), 17, colour=MUTED if style == 'Regular' else '#bdd1c0', latin=True)
        for i, item in enumerate(CHARACTERS):
            col, row = i % 9, i // 9
            centre, baseline = 126 + col*118, first_y + row*125
            text(centre, baseline, item['text'], 90, style, colour, anchor='ms')
        sentence = SENTENCES[0 if style == 'Regular' else 1]['text']
        text(72, sentence_y, sentence, 85 if style == 'Regular' else 73, style, colour)
    name = f'genzui-{VERSION}-okinawan.png'
    image.save(OUT/name, optimize=True)
    # Replace the former four-image set with the single composition.
    for suffix in ('characters-regular', 'characters-bold', 'sentences', 'weights'):
        (OUT/f'genzui-{VERSION}-okinawan-{suffix}.png').unlink(missing_ok=True)
    cards = [(name, '源萃明朝の沖縄語仮名18字をRegularとBoldで比較。上段は「ぬちどぅ たから。」、下段は「うや ゆし、くゎ ゆし。」の組見本。')]
    for lang in ('ja', 'en'):
        shutil.copyfile(ROOT/'release'/f'announcement-{VERSION}-{lang}.txt', OUT/f'announcement-{lang}.txt')
    manifest = {'version': VERSION, 'source': SOURCE_URL, 'pages': ['3-3'],
                'sentences': SENTENCES, 'characters': [{'label': e['label'], 'text': e['text'], 'codepoints': e['output']} for e in CHARACTERS], 'font_sha256': {s: hashlib.sha256(p.read_bytes()).hexdigest() for s, p in fonts.items()},
                'size': [2400, 2400], 'colour_mode': 'RGB',
                'note': 'Traditional proverbs. Punctuation and line breaks are editorial; kana digraphs are set as GenZui ligatures.'}
    manifest['images'] = [{'file': name, 'alt_ja': alt, 'sha256': hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name, alt in cards]
    (OUT/'specimens.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    (OUT/'alt-ja.txt').write_text('\n\n'.join(n+'\n'+alt for n, alt in cards)+'\n')
    page = '''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>源萃明朝 · SNS</title><style>*{box-sizing:border-box}body{margin:0;background:#f7f8f2;color:#25382e;font:16px/1.7 system-ui,sans-serif}main{max-width:1240px;margin:auto;padding:30px}a{color:#214e3c}.images{max-width:960px}figure{margin:0}img{width:100%;display:block}textarea{width:100%;min-height:220px;padding:16px;font:inherit;background:white;border:1px solid #cdd7cb}button{padding:8px 16px;font:inherit;background:#214e3c;color:white;border:0;cursor:pointer}p{color:#63776a}h1{font-size:28px}@media(max-width:700px){.images{grid-template-columns:1fr}main{padding:18px}}</style><main><a href="../">字形比較に戻る</a><h1>源萃明朝0.118 · SNS</h1><p>PNG・2400×2400px。</p><div class="images">'''
    for name, alt in cards:
        page += f'<figure><a href="{name}"><img src="{name}" alt="{html.escape(alt)}"></a><figcaption><a href="{name}" download>PNGを保存</a></figcaption></figure>'
    page += '</div>'
    for lang, label in [('ja', '日本語'), ('en', 'English')]:
        copy = (OUT/f'announcement-{lang}.txt').read_text()
        page += f'<h2>{label}</h2><textarea id="{lang}">{html.escape(copy)}</textarea><button data-copy="{lang}">Copy</button>'
    page += f'<p>ことわざの出典：<a href="{SOURCE_URL}">ハワイ大学「ことわざ」</a>、3-3頁。句読点と改行を整え、「どぅ・くゎ」を合字で表記。</p><p><a href="alt-ja.txt">画像の代替テキスト</a></p><span id="status" role="status"></span></main><script>document.querySelectorAll("[data-copy]").forEach(b=>b.onclick=async()=>{{const t=document.getElementById(b.dataset.copy);try{{await navigator.clipboard.writeText(t.value);document.getElementById("status").textContent="Copied."}}catch{{t.focus();t.select();document.getElementById("status").textContent="Select and copy the text."}}}})</script></html>'
    (OUT/'index.html').write_text(page)
    print('SNS: one 2400px character and sentence image, JA/EN copy, alt text and source record.')


if __name__ == '__main__':
    build()
