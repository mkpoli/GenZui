"""Funatsu kana composed from Noto's own hiragana strokes, and prefectural
raised katakana derived from Noto's own small katakana.

Mapping references describe character identity, not an upstream outline licence.
No outlines are imported from Nishiki-teki, Xim Sans or legacy Okinawan fonts.
"""
import json
import math
import pathops
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables
from fontTools.otlLib.builder import buildLigatureSubstSubtable
import okinawan_mincho
from sources import ROOT

DATA = json.loads((ROOT/'data/okinawan/mappings.json').read_text())
ENTRIES = DATA['characters']
PUA = {int(e['output'][0], 16): e for e in ENTRIES
       if len(e['output']) == 1 and 0xE000 <= int(e['output'][0], 16) <= 0xF8FF}
DESCRIPTIONS = {cp: (f"{e['label']}. " +
    ('Funatsu New Okinawan Kana; Nishiki-teki PUA convention. '
     'Composed by GenZui from Noto Serif JP hiragana strokes. ' if e['system'] == 'funatsu' else
     'Okinawa prefectural raised katakana; Xim Sans PUA convention. '
     'Reduced by GenZui from Noto Serif JP small katakana. ') +
    'This is a private-use mapping, not a Unicode assignment.')
    for cp, e in PUA.items()}

# Raised katakana: the Noto small kana each sign is reduced from, and the
# thickening that restores its stroke weight at the smaller size. ン has no
# small kana, so the full letter is reduced with more thickening. The signs
# fill at most a 420 x 380 box, top-aligned at 815, in a 500-unit advance.
RAISED = {
    0xE532: (0x30A1, 7), 0xE533: (0x30A3, 7), 0xE534: (0x30A5, 7),
    0xE535: (0x30A7, 7), 0xE536: (0x30A9, 7), 0xE537: (0x30C3, 7),
    0xE4EF: (0x31F7, 7), 0xE5AA: (0x30F3, 11),
}
RAISED_BOX = (420, 380)
RAISED_TOP = 815


def add_okinawan(font, add, make_glyph, contours, transform, add_feature):
    def unite(parts):
        # Union independently filled components: opposite native/custom winding
        # must not punch holes into a shared join.
        merged = pathops.Path()
        for part in parts:
            shape = pathops.Path()
            part.replay(shape.getPen())
            merged = pathops.op(merged, shape, pathops.PathOp.UNION)
        pen = RecordingPen()
        merged.draw(pen)
        return make_glyph([pen])

    def raised(source, radius):
        # The prefectural guide sets raised katakana as the text face's own
        # katakana at about half size, top-aligned with the line. Noto's
        # small kana already carry the optical correction for that size, so
        # each raised sign is the small kana reduced further, thickened by
        # uniting copies offset around a small circle, and moved to the top
        # of a half-width cell.
        pen = RecordingPen()
        font.getGlyphSet()[font.getBestCmap()[source]].draw(pen)
        shape = pathops.Path()
        pen.replay(shape.getPen())
        left, bottom, right, top = shape.bounds
        scale = min(RAISED_BOX[1] / (top - bottom), RAISED_BOX[0] / (right - left))
        reduced = pathops.Path()
        transform(pen, (scale, 0, 0, scale, 250 - scale * (left + right) / 2,
                        RAISED_TOP - scale * top)).replay(reduced.getPen())
        merged = pathops.Path()
        for k in range(12):
            angle = k * math.pi / 6
            moved = pathops.Path()
            reduced.draw(TransformPen(moved.getPen(), (1, 0, 0, 1, radius * math.cos(angle), radius * math.sin(angle))))
            merged = pathops.op(merged, moved, pathops.PathOp.UNION)
        out = RecordingPen()
        merged.draw(out)
        return [out]

    # The kit reads the source kana before any Okinawan glyph is added.
    kit = okinawan_mincho.Kit(font, contours, transform)
    recipes = okinawan_mincho.outlines(kit)
    recipes.update({cp: raised(source, radius) for cp, (source, radius) in RAISED.items()})
    for cp, parts in recipes.items():
        name = add(font, f'okinawa.u{cp:04X}', unite(parts))
        g = font['glyf'][name]
        raised_sign = PUA[cp]['system'] == 'prefecture'
        font['hmtx'][name] = (500 if raised_sign else 1000, g.xMin)
        font['vmtx'][name] = (500 if raised_sign else 1000, 880-g.yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format in (4, 12):
                table.cmap[cp] = name
    # Use a composition lookup so combining dakuten works even when a shaping
    # engine assigns an unknown script to the private-use base. The text stays
    # base + U+3099; the composed drawings are unencoded glyphs.
    # YI and YE stay with Noto's own い゙ and え゙ composition; only the
    # private-use bases need a composed drawing.
    mapping = {}
    cmap = font.getBestCmap()
    for e in ENTRIES:
        if len(e['output']) != 2 or int(e['output'][0], 16) not in recipes:
            continue
        cp = int(e['output'][0], 16)
        name = add(font, f"okinawa.{e['id']}", unite(okinawan_mincho.voiced(kit, recipes[cp])))
        font['vmtx'][name] = (1000, 880-font['glyf'][name].yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        mapping[(cmap[cp], cmap[0x3099])] = name
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildLigatureSubstSubtable(mapping)]
    lookup.SubTableCount = 1
    add_feature(font, 'GSUB', 'ccmp', lookup)
