"""Minnan kana tone letters and phonetic marks from FRB Taiwanese Kana.

The source outlines retain their 1000-unit em. GenZui supplies contextual
placement beside one to four fullwidth kana in vertical text. No kana outline
or advance is changed. Longer annotations can use separate ruby runs.
"""
import copy
import json

from fontTools.otlLib.builder import (buildAnchor, buildCoverage,
    buildMarkBasePosSubtable, buildSinglePosSubtable, buildValue)
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from repertoire import MINNAN_MARKS, MINNAN_TONES
from sources import ROOT


def source_font():
    return TTFont(ROOT/'sources/upstream/FRBTaiwaneseKana/FRBTaiwaneseKana.otf',
                  recalcTimestamp=False)


BOLD = json.loads((ROOT/'data/minnan/bold.json').read_text())['forms']


def closed(commands):
    """Drop a final line back to a contour's start, which closePath implies."""
    result, start = [], None
    for op, points in commands:
        if op == 'moveTo':
            start = points[0]
        if op == 'closePath' and result and result[-1] == ('lineTo', (start,)):
            result.pop()
        result.append((op, points))
    return result


def source_outline(source, cp, bold=False, matrix=(1, 0, 0, 1, 0, 0)):
    """The FRB outline, its Bold master drawn on the same points, or a blend.

    `bold` is False, True, or a fraction between the FRB outline (0) and the
    Bold master (1), for a face whose Bold kana gain less weight.
    """
    pen = TTGlyphPen(None)
    target = TransformPen(Cu2QuPen(pen, max_err=0.3, reverse_direction=True), matrix)
    if bold is True:
        parse_path(BOLD[f'U+{cp:04X}'], target)
    elif bold:
        regular, heavy = RecordingPen(), RecordingPen()
        source.getGlyphSet()[source.getBestCmap()[cp]].draw(regular)
        parse_path(BOLD[f'U+{cp:04X}'], heavy)
        commands = [closed(regular.value), closed(heavy.value)]
        assert [op for op, _ in commands[0]] == [op for op, _ in commands[1]], hex(cp)
        for (op, points), (_, bold_points) in zip(*commands):
            getattr(target, op)(*[(x+bold*(bx-x), y+bold*(by-y))
                                  for (x, y), (bx, by) in zip(points, bold_points)])
    else:
        source.getGlyphSet()[source.getBestCmap()[cp]].draw(target)
    return pen.glyph()


def import_forms(font, add, bold=False):
    source = source_font()
    assert source['head'].unitsPerEm == font['head'].unitsPerEm == 1000
    cmap = source.getBestCmap()
    added = {}
    for cp in (*MINNAN_TONES, *MINNAN_MARKS):
        name = add(font, f'minnan.u{cp:05X}', source_outline(source, cp, bold))
        font['hmtx'][name] = (source['hmtx'][cmap[cp]][0], font['glyf'][name].xMin)
        font['vmtx'][name] = (0 if cp in MINNAN_MARKS else 1000,
                              880-font['glyf'][name].yMax)
        added[cp] = name
    return added


def related_glyphs(font, names):
    """Include JP's vertical and ruby substitutions in contextual base classes."""
    names = set(names)
    mappings = []
    for lookup in font['GSUB'].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            if hasattr(sub, 'ExtSubTable'):
                sub = sub.ExtSubTable
            if hasattr(sub, 'mapping'):
                mappings.append(sub.mapping)
    while True:
        new = names | {dest for mapping in mappings for src, dest in mapping.items()
                       if src in names}
        if new == names:
            return names
        names = new


def contextual_substitution(font, bases, substitutions, count=1):
    """Build a chained single substitution; the caller chooses lookup flags."""
    single = otTables.Lookup()
    single.LookupType, single.LookupFlag = 1, 0
    mapping = otTables.SingleSubst(); mapping.mapping = substitutions
    single.SubTable, single.SubTableCount = [mapping], 1
    lookups = font['GSUB'].table.LookupList
    index = len(lookups.Lookup)
    lookups.Lookup.append(single); lookups.LookupCount = len(lookups.Lookup)
    sub = otTables.ChainContextSubst(); sub.Format = 3
    sub.BacktrackGlyphCount, sub.InputGlyphCount, sub.LookAheadGlyphCount = count, 1, 0
    sub.BacktrackCoverage = [buildCoverage(bases, font.getReverseGlyphMap()) for _ in range(count)]
    sub.InputCoverage = [buildCoverage(substitutions, font.getReverseGlyphMap())]
    sub.LookAheadCoverage = []
    record = otTables.SubstLookupRecord()
    record.SequenceIndex, record.LookupListIndex = 0, index
    sub.SubstCount, sub.SubstLookupRecord = 1, [record]
    return sub


def layout(font, add, add_feature, bold=False, edge_anchors=False):
    cmap = font.getBestCmap()
    kana_cps = {cp for cp in cmap if 0x30A1 <= cp <= 0x30FA or 0x31F0 <= cp <= 0x31FF}
    kana_cps |= {cp for cp in cmap if cp in (0x1B000, 0x1B155) or 0x1B120 <= cp <= 0x1B128 and cp != 0x1B123 or 0x1B164 <= cp <= 0x1B168}
    bases = related_glyphs(font, {cmap[cp] for cp in kana_cps})
    small_cps = {0x30A1, 0x30A3, 0x30A5, 0x30A7, 0x30A9, 0x30C3,
                 0x30E3, 0x30E5, 0x30E7, 0x30EE, 0x30F5, 0x30F6,
                 0x1B155, *range(0x31F0, 0x3200), *range(0x1B164, 0x1B169)}
    small = related_glyphs(font, {cmap[cp] for cp in small_cps if cp in cmap})
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    classes.update({cmap[cp]: 1 for cp in MINNAN_TONES})
    classes.update({cmap[cp]: 3 for cp in MINNAN_MARKS})

    # A narrower overline keeps its original thickness above small kana.
    source = source_font()
    short = add(font, 'minnan.overline.small', source_outline(
        source, 0x0305, bold, (.72, 0, 0, 1, 140, 0)))
    font['hmtx'][short] = (0, font['glyf'][short].xMin)
    font['vmtx'][short] = (0, 880-font['glyf'][short].yMax)
    classes[short] = 3
    lookup = otTables.Lookup(); lookup.LookupType, lookup.LookupFlag = 6, 0
    lookup.SubTable = []
    mark_names = {name for name, kind in classes.items() if kind == 3}
    for count in (2, 1, 0):
        sub = contextual_substitution(font, small, {cmap[0x0305]: short})
        sub.BacktrackCoverage = [buildCoverage(mark_names, font.getReverseGlyphMap())
                                 for _ in range(count)] + sub.BacktrackCoverage
        sub.BacktrackGlyphCount += count
        lookup.SubTable.append(sub)
    lookup.SubTableCount = len(lookup.SubTable)
    add_feature(font, 'GSUB', 'ccmp', lookup)
    # The overline hangs from its lower edge and the dot 46 units below its top,
    # the Regular FRB positions. With edge_anchors, a heavier outline keeps the
    # same clearance from the kana.
    over, dot = (font['glyf'][cmap[0x0305]].yMin, font['glyf'][cmap[0x0323]].yMax-46) if edge_anchors else (721, 380)
    marks = {cmap[0x0305]: (0, buildAnchor(505, over)),
             short: (0, buildAnchor(504, over)),
             cmap[0x0323]: (1, buildAnchor(500, dot))}
    anchors = {}
    for name in bases:
        g = font['glyf'][name]
        centre = round((g.xMin+g.xMax)/2)
        anchors[name] = {0: buildAnchor(centre, g.yMax+40),
                         1: buildAnchor(centre, g.yMin-80)}
    lookup = otTables.Lookup(); lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildMarkBasePosSubtable(marks, anchors, font.getReverseGlyphMap())]
    lookup.SubTableCount = 1
    add_feature(font, 'GPOS', 'mark', lookup)

    # Keep isolated tone letters in their own cells. After kana, use zero-advance
    # variants placed to the right, centred on the preceding one to four kana.
    tone_names = {cmap[cp] for cp in MINNAN_TONES}
    context = otTables.Lookup(); context.LookupType, context.LookupFlag = 6, 8
    context.SubTable = []
    positions = {}
    for count in (4, 3, 2, 1):
        mapping = {}
        for name in sorted(tone_names):
            alternate = add(font, name+f'.vert{count}', copy.deepcopy(font['glyf'][name]))
            font['hmtx'][alternate] = font['hmtx'][name]
            font['vmtx'][alternate] = (0, 880-font['glyf'][alternate].yMax)
            classes[alternate] = 1
            mapping[name] = alternate
            positions[alternate] = buildValue({'XPlacement': 740, 'YPlacement': 1000+(count-1)*500})
        context.SubTable.append(contextual_substitution(font, bases, mapping, count))
    context.SubTableCount = len(context.SubTable)
    add_feature(font, 'GSUB', 'vert', context)
    add_feature(font, 'GSUB', 'vrt2', copy.deepcopy(context))
    lookup = otTables.Lookup(); lookup.LookupType, lookup.LookupFlag = 1, 0
    lookup.SubTable = [buildSinglePosSubtable(positions, font.getReverseGlyphMap())]
    lookup.SubTableCount = 1
    # Placement is essential to these forms, so it stays enabled when optional
    # vertical kerning is off. Only variants selected by vert/vrt2 are affected.
    add_feature(font, 'GPOS', 'mark', lookup)
