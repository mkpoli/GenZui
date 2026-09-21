"""Complete squared-katakana coverage with native Noto unit-symbol components."""
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables

PAATU = 0x332C
DESCRIPTION = ('SQUARE PAATU combines the PA and prolonged mark from Noto Serif JP '
               'SQUARE PAASENTO (U+332B) with TSU from SQUARE HAITU (U+332A). '
               'Both writing directions retain the native small-kana components.')


def add_paatu(font, add, make_glyph, add_feature):
    """Append horizontal and vertical PAATU without changing existing glyph IDs."""
    cmap = font.getBestCmap()
    vertical = {}
    for record in font['GSUB'].table.FeatureList.FeatureRecord:
        if record.FeatureTag == 'vert':
            for index in record.Feature.LookupListIndex:
                for sub in font['GSUB'].table.LookupList.Lookup[index].SubTable:
                    vertical.update(getattr(sub, 'mapping', {}))

    def part(cp, indices, upright):
        name = cmap[cp]
        if upright:
            name = vertical[name]
        pen = RecordingPen()
        font.getGlyphSet()[name].draw(pen)
        result = RecordingPen()
        index = 0
        for op, args in pen.value:
            if index in indices:
                getattr(result, op)(*args)
            if op in ('closePath', 'endPath'):
                index += 1
        return result

    name = 'compat.u0332C'
    for upright, suffix, pa, tsu in (
        (False, '', range(5), range(4, 7)),
        (True, '.vert', range(5), range(3)),
    ):
        outline = make_glyph([part(0x332B, pa, upright), part(0x332A, tsu, upright)])
        add(font, name+suffix, outline)
        font['vmtx'][name+suffix] = (1000, 880-outline.yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name+suffix] = 1
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format in (4, 12):
            table.cmap[PAATU] = name
    sub = otTables.SingleSubst()
    sub.mapping = {name: name+'.vert'}
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    for tag in ('vert', 'vrt2'):
        add_feature(font, 'GSUB', tag, lookup)
