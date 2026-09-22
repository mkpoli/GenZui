"""Funatsu kana and prefectural raised katakana, drawn as complete strokes.

Mapping references describe character identity, not an upstream outline licence.
No outlines are imported from Nishiki-teki, Xim Sans or legacy Okinawan fonts.
"""
import json
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables
from fontTools.otlLib.builder import buildLigatureSubstSubtable
from okinawan_drawings import outlines, BASES, CANONICAL, DAKUTEN
from serif_forms import path
from sources import ROOT

DATA = json.loads((ROOT/'data/okinawan/mappings.json').read_text())
ENTRIES = DATA['characters']
PUA = {int(e['output'][0], 16): e for e in ENTRIES
       if len(e['output']) == 1 and 0xE000 <= int(e['output'][0], 16) <= 0xF8FF}
DESCRIPTIONS = {cp: (f"{e['label']}. " +
    ('Funatsu New Okinawan Kana; Nishiki-teki PUA convention. ' if e['system'] == 'funatsu' else
     'Okinawa prefectural raised katakana; Xim Sans PUA convention. ') +
    'Original GenZui drawing. This is a private-use mapping, not a Unicode assignment.')
    for cp, e in PUA.items()}


def add_okinawan(font, add, make_glyph, transform, add_feature):
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

    def fit(parts, base):
        # Joined letters share the vertical extent of the Noto kana they
        # extend, so they sit on the same baseline at the same size. They
        # are centred in the em and never wider than 920 units.
        shape = pathops.Path()
        for part in parts:
            part.replay(shape.getPen())
        left, bottom, right, top = shape.bounds
        targets = [font['glyf'][font.getBestCmap()[ord(c)]] for c in base]
        low, high = min(t.yMin for t in targets), max(t.yMax for t in targets)
        scale = min((high - low) / (top - bottom), 920 / (right - left))
        dx = 500 - scale * (left + right) / 2
        dy = low - scale * bottom
        return [transform(part, (scale, 0, 0, scale, dx, dy)) for part in parts]

    recipes = {cp: fit(parts, BASES[cp]) if cp in BASES else parts
               for cp, parts in outlines().items()}
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
    mapping, native_compositions = {}, {}
    cmap = font.getBestCmap()
    for e in ENTRIES:
        if len(e['output']) != 2:
            continue
        cp = int(e['output'][0], 16)

        base = recipes[cp] if cp in recipes else [path(stroke) for stroke in CANONICAL[cp]]
        name = add(font, f"okinawa.{e['id']}", unite([
            transform(p, (.90, 0, 0, 1, 12, 0)) for p in base]
            + [path(stroke) for stroke in DAKUTEN]))
        font['vmtx'][name] = (1000, 880-font['glyf'][name].yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        mapping[(cmap[cp], cmap[0x3099])] = name
        if cp in CANONICAL:
            # Noto already composes these two sequences in an earlier lookup.
            # Follow that composition with a substitution for the completed
            # glyph, preserving Noto's original lookup and outline.
            for existing in font['GSUB'].table.LookupList.Lookup:
                for subtable in existing.SubTable:
                    table = getattr(subtable, 'ExtSubTable', subtable)
                    for ligature in getattr(table, 'ligatures', {}).get(cmap[cp], []):
                        if ligature.Component == [cmap[0x3099]]:
                            native_compositions[ligature.LigGlyph] = name
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildLigatureSubstSubtable(mapping)]
    lookup.SubTableCount = 1
    add_feature(font, 'GSUB', 'ccmp', lookup)
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    subtable = otTables.SingleSubst()
    subtable.mapping = native_compositions
    lookup.SubTable, lookup.SubTableCount = [subtable], 1
    add_feature(font, 'GSUB', 'ccmp', lookup)
