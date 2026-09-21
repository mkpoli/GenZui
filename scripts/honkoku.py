"""Eleven transcription characters using Noto outlines and matching symbols."""
import copy
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import flagOverlapSimple
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

from sources import ROOT

TALLIES = tuple(range(0x1D372, 0x1D377))
NEW_IDCS = (0x2FFC, 0x2FFD, 0x2FFE, 0x2FFF, 0x31EF)
HONKOKU = (0x5344, *TALLIES, *NEW_IDCS)
SOURCE = ROOT/'sources/upstream/NotoSerifCJKjp/NotoSerifCJKjp-Regular.otf'
DESCRIPTIONS = {
    0x5344: 'Noto Serif CJK JP Regular supplies the ideograph 卄, with its original advance and vertical origin. Cubic outlines are converted to TrueType curves.',
    0x2FFC: 'The native Noto surround-from-left symbol is reflected horizontally, retaining its dashed frame.',
    0x2FFD: 'The native Noto surround-from-lower-left symbol is reflected horizontally, retaining its dashed frame.',
    0x2FFE: 'The native Noto dashed frame encloses a reduced Noto horizontal double-headed arrow.',
    0x2FFF: 'A clockwise half-turn arrow is drawn inside the native Noto dashed frame.',
    0x31EF: 'A minus sign is drawn inside the native Noto dashed frame, matching the frame stroke width.',
    **{cp: f'The first {i} stroke'+('s' if i > 1 else '')+' of Noto Serif JP 正, in writing order and at their original positions.'
       for i, cp in enumerate(TALLIES, 1)},
}


def add_honkoku(font, add, make_glyph, contours, transform):
    """Append the new characters, keeping all existing glyph IDs and mappings."""
    def part(cp, indices=None):
        return contours(font, cp, indices)

    def path(commands):
        pen = RecordingPen()
        parse_path(commands, pen)
        return pen

    # Noto's existing IDC frame has 30-unit strokes and 90-unit dashes.
    frame = part(0x2FF7, range(20))
    recipes = {
        0x2FFC: [transform(part(0x2FF7), (-1, 0, 0, 1, 1000, 0))],
        0x2FFD: [transform(part(0x2FFA), (-1, 0, 0, 1, 1000, 0))],
        0x2FFE: [frame, transform(part(0x2194), (.72, 0, 0, .72, 140, 106.4))],
        0x2FFF: [frame, path(
            'M470 710 C642 710 770 589 770 430 '
            'C770 268 620 126 361 126 '
            'L465 34 L441 8 L279 146 L441 284 L465 258 L353 158 '
            'C585 158 734 280 734 430 C734 570 625 674 470 674 Z')],
        0x31EF: [frame, path('M230 365 H770 V395 H230 Z')],
    }
    order = (0, 1, 3, 4, 2)  # 正: upper bar, upright, middle bar, left stem, foot.
    recipes.update({cp: [part(0x6B63, order[:i])]
                    for i, cp in enumerate(TALLIES, 1)})
    with TTFont(SOURCE) as donor:
        assert donor['head'].unitsPerEm == font['head'].unitsPerEm == 1000
        source_name = donor.getBestCmap()[0x5344]
        pen = RecordingPen()
        donor.getGlyphSet()[source_name].draw(pen)
        recipes[0x5344] = [pen]
        source_advance = donor['hmtx'][source_name][0]
        source_origin = donor['VORG'].VOriginRecords.get(source_name, donor['VORG'].defaultVertOriginY)
    for cp, parts in sorted(recipes.items()):
        if cp == TALLIES[-1]:
            outline = copy.deepcopy(font['glyf'][font.getBestCmap()[0x6B63]])
        elif cp in TALLIES:
            # Keep native strokes and their overlaps, as Noto does for 正.
            pen = TTGlyphPen(None)
            parts[0].replay(pen)
            outline = pen.glyph()
            outline.flags[0] |= flagOverlapSimple
            outline.recalcBounds(font['glyf'])
        else:
            outline = make_glyph(parts)
        name = add(font, f'honkoku.u{cp:05X}', outline)
        font['hmtx'][name] = (source_advance if cp == 0x5344 else 1000, outline.xMin)
        font['vmtx'][name] = (1000, (source_origin if cp == 0x5344 else 880)-outline.yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format in (4, 12) and (cp <= 0xFFFF or table.format == 12):
                table.cmap[cp] = name
