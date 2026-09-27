"""Funatsu kana and prefectural raised katakana, drawn from Noto components.

Mapping references describe character identity, not an upstream outline licence.
No outlines are imported from Nishiki-teki, Xim Sans or legacy Okinawan fonts.
"""
import json
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables
from fontTools.otlLib.builder import buildLigatureSubstSubtable
import okinawan_merge
from okinawan_ligatures import drawings as ligature_drawings
from sources import ROOT

DATA = json.loads((ROOT/'data/okinawan/mappings.json').read_text())
ENTRIES = DATA['characters']
PUA = {int(e['output'][0], 16): e for e in ENTRIES
       if len(e['output']) == 1 and 0xE000 <= int(e['output'][0], 16) <= 0xF8FF}
DESCRIPTIONS = {cp: (f"{e['label']}. " +
    ('Funatsu New Okinawan Kana; Nishiki-teki PUA convention. ' if e['system'] == 'funatsu' else
     'Okinawa prefectural raised katakana; Xim Sans PUA convention. ') +
    'GenZui drawing from Noto components. This is a private-use mapping, not a Unicode assignment.')
    for cp, e in PUA.items()}


def add_okinawan(font, add, make_glyph, contours, transform, add_feature,
                  bold=False):
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

    def part(ch, indices=None, matrix=None):
        pen = contours(font, ord(ch), indices)
        return transform(pen, matrix) if matrix else pen

    recipes = ligature_drawings(bold=bold)
    # The glottal letters and SI are Noto's own kana with a Noto stroke merged
    # into the outline (YA) or set beside it; see okinawan_merge. Bold reads
    # the same strokes from the wght 700 instance; the width given back to a
    # narrowed kana grows with Noto's own kana stems (77.8 to 125.3 units on
    # は's left stroke at wght 400 and 700).
    def beside(kana, params):
        if bold:
            params = dict(params, kana_bold=params['kana_bold'] * 125.3 / 77.8)
        return okinawan_merge.glottal_beside(font, contours, kana, **params)
    recipes.update({
        0xF45D: [okinawan_merge.glottal_ya(font, contours, **okinawan_merge.YA)],
        0xF45E: beside('ゆ', okinawan_merge.YU),
        0xF45F: beside('よ', okinawan_merge.YO),
        0xF460: beside('ゐわ', okinawan_merge.WA),
        0xF461: beside('ゐ', okinawan_merge.WI),
        0xF462: beside('ゑ', okinawan_merge.WE),
        0xF463: beside('ん', okinawan_merge.N),
        0xF467: beside('す', okinawan_merge.SI),
    })
    for cp, entry in PUA.items():
        if entry['system'] == 'prefecture':
            # Half-em advance, raised into the upper half of a full kana cell.
            recipes[cp] = [part(chr(int(entry['base'], 16)), matrix=(.48, 0, 0, .48, 10, 410))]
    for cp, parts in recipes.items():
        name = add(font, f'okinawa.u{cp:04X}', unite(parts))
        g = font['glyf'][name]
        raised = PUA[cp]['system'] == 'prefecture'
        font['hmtx'][name] = (500 if raised else 1000, g.xMin)
        font['vmtx'][name] = (500 if raised else 1000, 880-g.yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format in (4, 12):
                table.cmap[cp] = name
    # Use a composition lookup so combining dakuten works even when a shaping
    # engine assigns an unknown script to the private-use base. The text stays
    # base + U+3099; the composed drawings are unencoded glyphs.
    mapping = {}
    cmap = font.getBestCmap()
    for e in ENTRIES:
        if len(e['output']) != 2 or int(e['output'][0], 16) not in PUA:
            continue
        cp = int(e['output'][0], 16)

        original_mark = font['glyf'][cmap[0x309B]]
        mark = part('゛', matrix=(.72, 0, 0, .72, 810-.72*original_mark.xMin, 825-.72*original_mark.yMax))
        name = add(font, f"okinawa.{e['id']}", unite([
            transform(p, (.9, 0, 0, .9, 0, 0)) for p in recipes[cp]]+[mark]))
        font['vmtx'][name] = (1000, 880-font['glyf'][name].yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        mapping[(cmap[cp], cmap[0x3099])] = name
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildLigatureSubstSubtable(mapping)]
    lookup.SubTableCount = 1
    add_feature(font, 'GSUB', 'ccmp', lookup)
