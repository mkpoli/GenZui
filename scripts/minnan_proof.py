"""Build the Minnan layout specimen and archaic WU comparison."""
import base64
import html
import io

from fontTools import subset
from fontTools.ttLib import TTFont

from refinement_proof import drawing
from serif_forms import wu_alternate
from fontTools.pens.svgPathPen import SVGPathPen
from repertoire import MINNAN_TONES, repertoire
from serif import OUT, STEM, VERSION
from sources import ROOT


def build_study():
    after = TTFont(OUT/(STEM+'.ttf'), recalcTimestamp=False)
    names = {ord(item['character']): item['name'] for item in repertoire()}
    cards = []
    for cp in MINNAN_TONES:
        title = names[cp].removeprefix('KATAKANA LETTER MINNAN ')
        cards.append(f'<article class="tone-card"><span class="code">U+{cp:X}</span>'
                     f'<div class="tone face" lang="ja">{chr(cp)}</div>'
                     f'<h3>{html.escape(title.title())}</h3></article>')
    # Keep the page compact; layout closure preserves tone and mark variants.
    points = {0x0305, 0x0323, 0x3000, 0x1B11F, *MINNAN_TONES,
              *range(0x3040, 0x3100), *map(ord, '源萃明朝恬聽 0123456789')}
    options = subset.Options(); options.recalc_timestamp = False
    options.layout_features = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=points); sub.subset(after)
    after.flavor = 'woff2'; stream = io.BytesIO(); after.save(stream)
    pen = SVGPathPen(after.getGlyphSet())
    after.getGlyphSet()[wu_alternate(after)].draw(pen)
    hooked_svg = drawing(after,0x1B11F)
    import re
    # Replace only the outline, retaining the same em and baseline guides.
    hooked_svg = re.sub(r'(<path class="outline"[^>]* d=")[^"]*', lambda m:m[1]+html.escape(pen.getCommands()), hooked_svg)
    page = (ROOT/'templates/minnan.html').read_text()
    for token, value in {
        '{{FONT}}': base64.b64encode(stream.getvalue()).decode(),
        '{{VERSION}}': VERSION, '{{TONES}}': ''.join(cards),
        '{{HOOKED_WU}}': hooked_svg,
        '{{AFTER_WU}}': drawing(after, 0x1B11F),
    }.items():
        page = page.replace(token, value)
    assert '{{' not in page and '/home/' not in page
    return page
