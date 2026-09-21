"""Build an offline comparison of the ten 0.101 outline revisions."""
import base64
import hashlib
import html
import io
import json

from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from serif import OUT, STEM, VERSION
from serif_forms import DESCRIPTIONS, REVISED
from sources import ROOT

NAMES = {0x1B123:'Hiragana KOTO', 0x1B124:'Katakana TOKI',
         0x1B125:'Katakana TOTE', 0x1B126:'Katakana YORI',
         0x1B127:'Alternate NE', 0x1B128:'Alternate WI',
         0x2A708:'Katakana TOMO', 0x2CF02:'Hiragana NARI',
         0x2CF00:'Katakana SHITE', 0x2CEFF:'Katakana NARI'}


def drawing(font, cp):
    gs = font.getGlyphSet()
    pen = SVGPathPen(gs)
    gs[font.getBestCmap()[cp]].draw(pen)
    return ('<svg viewBox="0 0 1000 1000" aria-hidden="true">'
            '<g class="guides"><path d="M0 880H1000 M0 120H1000"/>'
            '<path class="centre" d="M500 0V1000"/></g>'
            '<path class="outline" transform="translate(0 880) scale(1 -1)" '
            f'd="{html.escape(pen.getCommands())}"/></svg>')


def build_comparison():
    baseline = ROOT/'research/baselines'
    raw = (baseline/'GenZui-0.100-review.woff2').read_bytes()
    manifest = json.loads((baseline/'baseline.json').read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest['subset_woff2_sha256']
    before = TTFont(io.BytesIO(raw))
    after = TTFont(OUT/(STEM+'.ttf'), recalcTimestamp=False)
    cards = []
    for cp in REVISED:
        name, ch = NAMES[cp], chr(cp)
        context = f'あ{ch}い ん{ch}り' if cp in (0x1B123,0x2CF02) else f'ア{ch}イ カ{ch}ナ'
        pairs = []
        for label, font, css in (('0.100',before,'before'),(VERSION,after,'after')):
            pairs.append(f'<div class="sample {css}"><h3>{label}</h3>{drawing(font,cp)}'
                         f'<p class="context" lang="ja">{context}</p></div>')
        cards.append(f'<article><div class="card-head"><h2>{name}</h2><span>U+{cp:05X}</span></div>'
                     f'<div class="pair">{"".join(pairs)}</div>'
                     f'<p class="description">{html.escape(DESCRIPTIONS[cp])}</p></article>')
    options = subset.Options(); options.recalc_timestamp = False
    options.name_IDs = ['*']; options.name_legacy = True; options.name_languages = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=before.getBestCmap())
    sub.subset(after); after.flavor = 'woff2'
    stream = io.BytesIO(); after.save(stream)
    page = (ROOT/'templates/refinements.html').read_text()
    for key, value in {
        '{{BEFORE_FONT}}':base64.b64encode(raw).decode(),
        '{{AFTER_FONT}}':base64.b64encode(stream.getvalue()).decode(),
        '{{VERSION}}':VERSION, '{{CARDS}}':''.join(cards),
        '{{BEFORE_NOTICE}}':html.escape((baseline/'NOTICE-0.100.txt').read_text()),
    }.items(): page = page.replace(key, value)
    assert '{{' not in page and '/home/' not in page
    return page


if __name__ == '__main__':
    (OUT/'refinements.html').write_text(build_comparison())
    print('Built ten-character before/after comparison.')
