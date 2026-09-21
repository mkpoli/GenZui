"""Build a focused gallery of GenZui constructions and optical adaptations."""
import base64
import hashlib
import html
import io
import json

from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from refinement_proof import NAMES
from serif import OUT, SMALL, STEM, VERSION
from serif_forms import DESCRIPTIONS, REVISION_0112, wu_alternate
from sources import ROOT

REFERENCES = {0x1B124:'トキ', 0x2A708:'トモ', 0x1B123:'こと', 0x2CEFF:'シリ',
              0x2CF02:'んえへ', 0x2CF00:'シノ', 0x1B11F:'けほ', 0x1B125:'トテ',
              0x1B126:'ヨリ', 0x1B127:'ネヰ', 0x1B128:'ナヰ'}

REVIEW_FORMS = REVISION_0112

APPROVED = {0x1B11F, 0x1B123, 0x1B126, 0x2A708, 0x2CF00, 0x2CEFF, 0x1B128}


def contexts(cp):
    hira = cp in (0x1B11F,0x1B123,0x2CF02,0x1B132,0x1B150,0x1B151,0x1B152)
    if cp in (0x1B124, 0x1B125):
        lines = ['𪜈𛄥𛄤', 'ア'+chr(cp)+'イ', 'トモテキ']
    elif cp == 0x2A708:
        lines = ['𛄤𪜈𛄥', 'ト𪜈モ', 'ア𪜈イ']
    elif cp == 0x2CF02:
        lines = ['ん𬼂え', 'へ𬼂へ', 'あ𬼂い']
    elif cp == 0x1B123:
        lines = ['と𛄣を', 'て𛄣あ', 'この𛄣を']
    elif cp == 0x1B11F:
        lines = ['け𛄟ほ', 'あ𛄟い']
    else:
        refs = REFERENCES.get(cp, chr(SMALL[cp]) if cp in SMALL else '')
        lines = [refs[0]+chr(cp)+refs[-1], ('あ' if hira else 'ア')+chr(cp)+('い' if hira else 'イ')]
    text = ''.join(f'<span>{line}</span>' for line in lines)
    return (f'<div class="contexts"><div class="context horizontal"><h4>Horizontal</h4>'
            f'<div class="reading horizontal-reading" lang="ja">{text}</div></div>'
            f'<div class="context vertical"><h4>Vertical</h4>'
            f'<div class="reading vertical-reading" lang="ja">{text}</div></div></div>')


def comparison(font, cp, before):
    return (f'<div class="current-outline">{drawing(font,cp,before)}</div>'
            f'<div class="previous-outline">{drawing(before,cp)}</div>'+contexts(cp))


def outline(font, cp, name=None, css=''):
    gs = font.getGlyphSet(); pen = SVGPathPen(gs)
    gs[name or font.getBestCmap()[cp]].draw(pen)
    return f'<path class="outline {css}" transform="translate(0 880) scale(1 -1)" d="{html.escape(pen.getCommands())}"/>'


def shape_names(font, cp):
    default = font.getBestCmap()[cp]
    if cp != 0x1B11F:
        return default, None
    alternate = wu_alternate(font)
    return default, alternate


def drawing(font, cp, old=None):
    paths = ''
    if old:
        curved, hooked = shape_names(old, cp)
        paths += outline(old, cp, curved, 'overlay-old default-overlay')
        if hooked:
            paths += outline(old, cp, hooked, 'overlay-old alternate-overlay')
    curved, hooked = shape_names(font, cp)
    paths += outline(font, cp, curved, 'default-shape')
    if hooked:
        paths += outline(font, cp, hooked, 'alternate-shape')
    return ('<svg viewBox="0 0 1000 1000" aria-hidden="true">'
            '<g class="guides"><path d="M0 880H1000 M0 120H1000 M500 0V1000"/></g>'
            + paths + '</svg>')


def historical_reference(cp):
    if cp not in (0x2CEFF, 0x2CF02):
        return ''
    name, label, url = (
        ('nari-katakana-1899', '藤井乙男『操觚便覧』(1899), p. 16', 'https://dl.ndl.go.jp/pid/863176/1/12')
        if cp == 0x2CEFF else
        ('nari-hiragana-1902', '糸左近『和漢の文典：雅俗対照』(1902), p. 60', 'https://dl.ndl.go.jp/pid/864212/1/36'))
    raw = base64.b64encode((ROOT/'research/specimens'/(name+'.jpg')).read_bytes()).decode()
    return (f'<figure class="historical-reference"><a href="{url}"><img src="data:image/jpeg;base64,{raw}" '
            f'alt="Printed historical NARI specimen from {html.escape(label)}" loading="lazy"></a>'
            f'<figcaption><a href="{url}">{label}</a><br>National Diet Library · public domain</figcaption></figure>')


def stroke_references(font, cp):
    if cp == 0x1B11F:
        chars = 'かカ'
        caption = ('Noto か and カ show the turn and taper of a kana hook. '
                   'WU has a narrower drawn return, set farther right. Its lower '
                   'stem maintains its weight through the bend before tapering '
                   'toward the tip.')
    elif cp == 0x2A708:
        chars = 'にほモ'
        caption = ('In Noto に and ほ, the left head and right stroke entry have '
                   'more space between them. TOMO lowers and shortens MO’s '
                   'upturned entry while retaining the gap beside TO.')
    elif cp == 0x2CF02:
        chars = 'えへ'
        caption = ('Noto え supplies the rounded right finish. The shoulder and '
                   'descending wave carry fuller, more even weight; the upper '
                   'diagonal is unchanged.')
    else:
        return ''
    glyphs = ''.join('<figure>'+drawing(font,ord(ch))+'<figcaption>'+ch+'</figcaption></figure>' for ch in chars)
    return '<div class="stroke-study"><h4>Noto kana references</h4><div class="stroke-glyphs">'+glyphs+'</div><p>'+caption+'</p></div>'


def webfont(font, points):
    options = subset.Options(); options.recalc_timestamp = False
    options.name_IDs = ['*']; options.name_languages = ['*']
    options.layout_features = ['*']
    sub = subset.Subsetter(options=options); sub.populate(unicodes=points); sub.subset(font)
    font.flavor = 'woff2'; stream = io.BytesIO(); font.save(stream)
    return stream.getvalue()


def build_gallery(public=False):
    folder = ROOT/'research/baselines'
    raw = (folder/'GenZui-0.111-gallery.woff2').read_bytes()
    manifest = json.loads((folder/'gallery-0.111.json').read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest['subset_woff2_sha256']
    before = TTFont(io.BytesIO(raw))
    after = TTFont(OUT/(STEM+'.ttf'), recalcTimestamp=False)
    sources = json.loads((OUT/'sources.json').read_text())
    own = {int(cp[2:],16) for cp, kind in sources['source_kinds'].items() if kind == 'genzui'}
    assert own == set(DESCRIPTIONS) | set(SMALL) and len(own) == 21
    order = [*REVIEW_FORMS, *sorted(own-set(REVIEW_FORMS))]
    cards = []
    for cp in order:
        small = cp in SMALL
        title = ('Small '+chr(SMALL[cp])) if small else NAMES.get(cp, 'Archaic hiragana WU')
        ref = chr(SMALL[cp]) if small else REFERENCES[cp]
        group = 'small' if small else 'drawn'
        chart = '1B130' if small else '2A700' if cp == 0x2A708 else '2CEB0' if cp > 0x20000 else '1B100'
        if public:
            from release_copy import FORM_DESCRIPTIONS
        note = ('Weight-500 Noto source at 72% scale, with adjusted small-kana positioning.' if small
                else (FORM_DESCRIPTIONS if public else DESCRIPTIONS)[cp])
        previous = '<span class="revision approved">Accepted</span>' if cp in APPROVED else '<span class="revision">Revised</span>' if cp in REVIEW_FORMS else ''
        if public:
            previous = ''
        history = ''
        if cp in (0x1B123,0x1B124,0x1B125,0x1B126,0x2A708,0x2CEFF,0x2CF00,0x2CF02):
            history = '<a href="https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf">Historical specimens · L2/24-150</a>'
        elif cp == 0x1B11F:
            history = '<a href="https://www.unicode.org/L2/L2020/20152-archaic-wu-origin.pdf">WU origins · L2/20-152</a>'
        single = public or cp not in REVIEW_FORMS
        if single:
            specimens = (f'<div class="pair single"><div class="sample current">'
                         f'<div class="sample-heading"><h3>GenZui · {VERSION}</h3></div>'
                         + drawing(after,cp)+contexts(cp)+'</div></div>')
        else:
            specimens = (f'<div class="pair"><div class="sample before"><div class="sample-heading"><h3>Previous · 0.111</h3></div>{drawing(before,cp)}{contexts(cp)}</div>'
                         f'<div class="sample current"><div class="sample-heading"><h3>GenZui · <span class="version-label" aria-live="polite">{VERSION}</span></h3>'
                         f'<button type="button" class="swap" aria-pressed="false" data-current="{VERSION}" data-previous="0.111">Swap to 0.111</button></div>'
                         f'{comparison(after,cp,before)}</div></div>')
        source_note = note if public else sources['added'][f'U+{cp:04X}']
        cards.append(f'''<article class="glyph-card" id="u{cp:x}" data-kind="{group}" data-revised="{str(cp in REVIEW_FORMS).lower()}">
<div class="card-heading"><h2>{html.escape(title)}</h2><div><span class="code">U+{cp:X}</span>{previous}</div></div>
{specimens}
<p class="description">{html.escape(note)}</p>
<details><summary>Construction & references</summary><div class="reference"><span class="current native" lang="ja">{ref}</span><p>Stroke reference · Noto Serif {'Hentaigana' if cp==0x1B168 else 'JP'}<br>{html.escape(source_note)}</p></div><div class="reference-links"><a href="https://www.unicode.org/charts/PDF/Unicode-18.0/U180-{chart}.pdf">Unicode character chart</a>{history}</div>{stroke_references(after,cp)}{historical_reference(cp)}</details></article>''')
    current = webfont(after, before.getBestCmap())
    page = (ROOT/'templates'/('gallery-public.html' if public else 'gallery.html')).read_text()
    for key, value in {'{{VERSION}}':VERSION, '{{REVISED_COUNT}}':str(len(REVIEW_FORMS)), '{{CARDS}}':''.join(cards),
        '{{WU_CONTEXT}}':contexts(0x1B11F),
        '{{FONT}}':base64.b64encode(current).decode(), '{{BEFORE_FONT}}':base64.b64encode(raw).decode(),
        '{{CSS}}':(ROOT/'site/gallery.css').read_text(), '{{JS}}':(ROOT/'site/gallery.js').read_text()}.items():
        page = page.replace(key,value)
    assert '{{' not in page and '/home/' not in page
    return page


if __name__ == '__main__':
    (OUT/'gallery.html').write_text(build_gallery())
