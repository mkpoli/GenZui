"""Build GenZui Serif from pinned Noto and FRB sources with drawn kana."""
import base64
import copy
import html
import json
import shutil

from fontTools import subset
from fontTools.otlLib.builder import buildAnchor, buildCoverage, buildMarkBasePosSubtable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont
import pathops

from repertoire import MINNAN_MARKS, MINNAN_TONES, font_path, repertoire
from minnan import import_forms as import_minnan, layout as layout_minnan
from serif_forms import DESCRIPTIONS, REVISED, REVISION_0103, REVISION_0104, REVISION_0105, REVISION_0106, REVISION_0107, REVISION_0108, REVISION_0109, REVISION_0110, REVISION_0111, REVISION_0112, REVISION_0115, REVISION_0117, DENSE_WEIGHT, hooked_wu, refinements
from sources import ROOT, verify
from compatibility import PAATU, DESCRIPTION as PAATU_DESCRIPTION, add_paatu
from honkoku import HONKOKU, TALLIES, DESCRIPTIONS as HONKOKU_DESCRIPTIONS, SOURCE as CJK_SOURCE, add_honkoku
from okinawan import add_okinawan, PUA as OKINAWAN_PUA, DESCRIPTIONS as OKINAWAN_DESCRIPTIONS, ENTRIES as OKINAWAN_ENTRIES
from gugyeol import add_gugyeol, PUA as GUGYEOL_PUA

CJK_BOLD = CJK_SOURCE.with_name('NotoSerifCJKjp-Bold.otf')

OUT = ROOT / 'build/serif'
FAMILY = 'GenZui Serif'
FAMILY_JA = '源萃明朝'
STEM = 'GenZuiSerif-Regular'
BOLD_STEM = 'GenZuiSerif-Bold'
VERSION = '0.117'
# One archive carries both faces.
PACKAGE = f'GenZuiSerif-{VERSION}.zip'
SMALL = {0x1B132: 0x3053, 0x1B150: 0x3090, 0x1B151: 0x3091,
         0x1B152: 0x3092, 0x1B155: 0x30B3, 0x1B164: 0x30F0,
         0x1B165: 0x30F1, 0x1B166: 0x30F2, 0x1B167: 0x30F3,
         0x1B168: 0x1B121}
PROVENANCE = {}


def import_glyph(font, source, name):
    """Keep donor names and component references separate from the JP glyphs."""
    target = 'hist.' + name
    if target in font['glyf']:
        return target
    outline = copy.deepcopy(source['glyf'][name])
    if outline.isComposite():
        for component in outline.components:
            component.glyphName = import_glyph(font, source, component.glyphName)
    add(font, target, outline)
    font['hmtx'][target] = source['hmtx'][name]
    return target


def instance(family, weight, points=None):
    font = TTFont(font_path(family), recalcTimestamp=False)
    if points is not None:
        options = subset.Options()
        options.recalc_timestamp = False
        options.name_IDs = ['*']
        sub = subset.Subsetter(options=options)
        sub.populate(unicodes=points)
        sub.subset(font)
    return instantiateVariableFont(font, {'wght': weight}, inplace=True)


def contours(font, cp, indices=None):
    glyphs = font.getGlyphSet()
    pen = RecordingPen()
    glyphs[font.getBestCmap()[cp]].draw(pen)
    result, current = [], []
    for op, args in pen.value:
        current.append((op, args))
        if op in ('closePath', 'endPath'):
            result.append(current)
            current = []
    out = RecordingPen()
    out.value = [item for i, contour in enumerate(result)
                 if indices is None or i in indices for item in contour]
    return out


def transform(outline, matrix):
    result = RecordingPen()
    outline.replay(TransformPen(result, matrix))
    return result


def glyph(parts):
    shape = pathops.Path()
    for part in parts:
        part.replay(shape.getPen())
    shape = pathops.simplify(shape)
    pen = TTGlyphPen(None)
    shape.draw(Cu2QuPen(pen, max_err=0.3, reverse_direction=False))
    return pen.glyph()


def add(font, name, outline):
    font.setGlyphOrder(font.getGlyphOrder() + [name])
    font['glyf'][name] = outline
    outline.recalcBounds(font['glyf'])
    font['hmtx'][name] = (1000, outline.xMin)
    return name


def add_feature(font, table_tag, feature_tag, lookup):
    if table_tag not in font:
        table = newTable(table_tag)
        table.table = getattr(otTables, table_tag)()
        table.table.Version = 0x00010000
        table.table.LookupList = otTables.LookupList()
        table.table.LookupList.Lookup = []
        table.table.FeatureList = otTables.FeatureList()
        table.table.FeatureList.FeatureRecord = []
        table.table.ScriptList = otTables.ScriptList()
        table.table.ScriptList.ScriptRecord = []
        font[table_tag] = table
    table = font[table_tag].table
    index = len(table.LookupList.Lookup)
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    matches = [i for i, record in enumerate(table.FeatureList.FeatureRecord)
               if record.FeatureTag == feature_tag]
    if matches:
        feature_index = matches[0]
        for i in matches:
            feature = table.FeatureList.FeatureRecord[i].Feature
            feature.LookupListIndex.append(index)
            feature.LookupCount = len(feature.LookupListIndex)
    else:
        feature = otTables.FeatureRecord()
        feature.FeatureTag = feature_tag
        feature.Feature = otTables.Feature()
        feature.Feature.FeatureParams = None
        feature.Feature.LookupListIndex = [index]
        feature.Feature.LookupCount = 1
        feature_index = len(table.FeatureList.FeatureRecord)
        table.FeatureList.FeatureRecord.append(feature)
    for tag in ('DFLT', 'kana', 'hira'):
        if not any(s.ScriptTag == tag for s in table.ScriptList.ScriptRecord):
            record = otTables.ScriptRecord()
            record.ScriptTag = tag
            record.Script = otTables.Script()
            record.Script.LangSysRecord = []
            record.Script.LangSysCount = 0
            record.Script.DefaultLangSys = otTables.LangSys()
            lang = record.Script.DefaultLangSys
            lang.LookupOrder = None
            lang.ReqFeatureIndex = 0xFFFF
            lang.FeatureIndex = []
            lang.FeatureCount = 0
            table.ScriptList.ScriptRecord.append(record)
    # Make the feature available under every language system, including Latin
    # runs where an older shaping engine treats new kana as unassigned.
    for script in table.ScriptList.ScriptRecord:
        langs = [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]
        for lang in filter(None, langs):
            if not any(table.FeatureList.FeatureRecord[i].FeatureTag == feature_tag for i in lang.FeatureIndex):
                lang.FeatureIndex.append(feature_index)
    records = table.FeatureList.FeatureRecord
    order = sorted(range(len(records)), key=lambda i: records[i].FeatureTag)
    remap = {old: new for new, old in enumerate(order)}
    table.FeatureList.FeatureRecord = [records[i] for i in order]
    table.FeatureList.FeatureCount = len(records)
    for script in table.ScriptList.ScriptRecord:
        langs = [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]
        for lang in filter(None, langs):
            lang.FeatureIndex = sorted(remap[i] for i in lang.FeatureIndex)
            lang.FeatureCount = len(lang.FeatureIndex)
            if lang.ReqFeatureIndex != 0xFFFF:
                lang.ReqFeatureIndex = remap[lang.ReqFeatureIndex]
    table.ScriptList.ScriptRecord.sort(key=lambda s: s.ScriptTag)
    table.ScriptList.ScriptCount = len(table.ScriptList.ScriptRecord)


def layout(font, donor, vertical, points, alternates=(), mark_anchor_x=830, mark_drop=626):
    cmap = font.getBestCmap()
    bases = {cmap[cp] for cp in points} | set(vertical.values()) | set(alternates)
    marks, mark_mapping = {}, {}
    for cp in (0x3099, 0x309A):
        name = import_glyph(font, donor, donor.getBestCmap()[cp])
        mark_mapping[cmap[cp]] = name
        vname = add(font, name+'.vert', copy.deepcopy(font['glyf'][name]))
        font['hmtx'][vname] = font['hmtx'][name]
        vertical[name] = vname
        marks[name] = (0, buildAnchor(0, 0))
        marks[vname] = (1, buildAnchor(0, 0))

    # Use the donor marks only after a historical base. Ordinary JP text keeps
    # its original marks, composition, anchors and vertical substitutions.
    single = otTables.Lookup()
    single.LookupType, single.LookupFlag = 1, 0
    sub = otTables.SingleSubst()
    sub.mapping = mark_mapping
    single.SubTable, single.SubTableCount = [sub], 1
    lookups = font['GSUB'].table.LookupList
    substitution_index = len(lookups.Lookup)
    lookups.Lookup.append(single)
    lookups.LookupCount = len(lookups.Lookup)
    context = otTables.ChainContextSubst()
    context.Format = 3
    context.BacktrackGlyphCount = context.InputGlyphCount = 1
    context.BacktrackCoverage = [buildCoverage(bases, font.getReverseGlyphMap())]
    context.InputCoverage = [buildCoverage(mark_mapping, font.getReverseGlyphMap())]
    context.LookAheadGlyphCount, context.LookAheadCoverage = 0, []
    record = otTables.SubstLookupRecord()
    record.SequenceIndex, record.LookupListIndex = 0, substitution_index
    context.SubstCount, context.SubstLookupRecord = 1, [record]
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 6, 0
    lookup.SubTable, lookup.SubTableCount = [context], 1
    add_feature(font, 'GSUB', 'ccmp', lookup)

    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    sub = otTables.SingleSubst()
    sub.mapping = vertical
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    add_feature(font, 'GSUB', 'vert', lookup)
    add_feature(font, 'GSUB', 'vrt2', copy.deepcopy(lookup))
    anchors = {}
    for name in bases:
        g = font['glyf'][name]
        # Keep both marks clear of the top outline and within the em's width.
        anchors[name] = {0: buildAnchor(mark_anchor_x, g.yMax - mark_drop),
                         1: buildAnchor(g.xMax + 148, 0)}
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildMarkBasePosSubtable(marks, anchors, font.getReverseGlyphMap())]
    lookup.SubTableCount = 1
    add_feature(font, 'GPOS', 'mark', lookup)
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    classes.update({name: 1 for name in bases})
    classes.update({name: 3 for name in marks})
    for name in font.getGlyphOrder():
        if name not in font['vmtx'].metrics:
            font['vmtx'][name] = (0 if name in marks else 1000,
                                880 - getattr(font['glyf'][name], 'yMax', 0))
    # Includes the highest positioned mark; Windows must not clip it.
    top = max(font['glyf'][name].yMax + 252 + 626 - mark_drop for name in bases)
    font['OS/2'].usWinAscent = max(font['OS/2'].usWinAscent, top)


def build(weight=400):
    """Build one static face. 400 is Regular. 700 is Bold, the named Noto instance."""
    verify()
    PROVENANCE.clear()
    OUT.mkdir(parents=True, exist_ok=True)
    style = 'Regular' if weight == 400 else 'Bold'
    stem = 'GenZuiSerif-' + style
    # Small forms are scaled from one step above the text weight, as Regular
    # scales weight 500 rather than 400. Bold scales weight 800.
    small_weight = 500 if weight == 400 else 800
    print(f'Instantiating Noto Serif JP at weight {weight}', flush=True)
    font = jp = instance('NotoSerifJP', weight)
    heavier = instance('NotoSerifJP', small_weight, set(SMALL.values()) - {0x1B121})
    h_heavier = instance('NotoSerifHentaigana', small_weight, {0x1B121})
    donor = instance('NotoSerifHentaigana', weight)
    originals = set(font.getBestCmap())
    points = {ord(item['character']) for item in repertoire()}
    historical = points - originals - {PAATU} - set(HONKOKU)
    cmap_add = {cp: import_glyph(font, donor, donor.getBestCmap()[cp])
                for cp in sorted(historical & set(donor.getBestCmap()))}
    retained = len(cmap_add)
    minnan_points = set(MINNAN_TONES) | set(MINNAN_MARKS)
    cmap_add.update(import_minnan(font, add, weight >= 700))
    frb = 'FRB Taiwanese Kana outline' if weight == 400 else 'GenZui Bold master of the FRB Taiwanese Kana outline'
    for cp in minnan_points:
        PROVENANCE[f'U+{cp:04X}'] = (f'{frb}; GenZui kana mark attachment.'
            if cp in MINNAN_MARKS else f'{frb}; 500-unit horizontal advance and contextual vertical placement.')
    # Drawings take their native strokes from the instance being built.
    def part(ch, indices=None):
        return contours(jp, ord(ch), indices)
    recipes = {}
    dense = instance('NotoSerifJP', DENSE_WEIGHT, {ord('リ')}) if weight >= 700 else jp
    recipes.update(refinements(part, transform, weight >= 700,
                               lambda ch, indices=None: contours(dense, ord(ch), indices)))
    descriptions = dict(DESCRIPTIONS)
    vertical = {}
    for cp, source_cp in SMALL.items():
        source = h_heavier if cp == 0x1B168 else heavier
        # One step above the text weight, then scale 0.72, so small forms keep
        # more substance than a literal reduction. Positioning follows JP small kana.
        recipes[cp] = [transform(contours(source, source_cp), (.72,0,0,.72,140,-25))]
        descriptions[cp] = f'Noto Serif {"Hentaigana" if cp == 0x1B168 else "JP"} U+{source_cp:04X}, weight {small_weight}, scale 0.72.'
    for cp, parts in sorted(recipes.items()):
        name = f'hist.u{cp:05X}'
        add(font, name, glyph(parts))
        cmap_add[cp] = name
        if cp in SMALL:
            vertical[name] = add(font, name+'.vert', glyph([transform(p, (1,0,0,1,140,190)) for p in parts]))
        PROVENANCE[f'U+{cp:04X}'] = descriptions[cp]
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format in (4, 12):
            table.cmap.update({cp: name for cp, name in cmap_add.items()
                               if cp <= (0xFFFF if table.format == 4 else 0x10FFFF)})
    alternate = add(font, 'hist.u1B11F.ss01', glyph(hooked_wu(part, transform, weight >= 700)))
    sub = otTables.SingleSubst()
    sub.mapping = {cmap_add[0x1B11F]: alternate}
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    add_feature(font, 'GSUB', 'ss01', lookup)
    params = otTables.FeatureParamsStylisticSet()
    params.Version = 0
    params.UINameID = font['name'].addName('Hooked WU')
    font['name'].setName('うの鉤形', params.UINameID, 3, 1, 0x411)
    next(r for r in font['GSUB'].table.FeatureList.FeatureRecord
         if r.FeatureTag == 'ss01').Feature.FeatureParams = params
    layout(font, donor, vertical, historical-minnan_points, [alternate])
    layout_minnan(font, add, add_feature, weight >= 700)
    add_paatu(font, add, glyph, add_feature)
    PROVENANCE[f'U+{PAATU:04X}'] = PAATU_DESCRIPTION
    add_honkoku(font, add, glyph, contours, transform,
                source=CJK_SOURCE if weight == 400 else CJK_BOLD)
    PROVENANCE.update({f'U+{cp:04X}': value for cp, value in HONKOKU_DESCRIPTIONS.items()})
    if weight != 400:
        PROVENANCE[f'U+{0x5344:04X}'] = HONKOKU_DESCRIPTIONS[0x5344].replace('Regular', 'Bold')
    add_okinawan(font, add, glyph, contours, transform, add_feature, weight >= 700)
    PROVENANCE.update({f'U+{cp:04X}': value for cp, value in OKINAWAN_DESCRIPTIONS.items()})
    gugyeol_descriptions = add_gugyeol(font, add, glyph,
        CJK_SOURCE if weight == 400 else CJK_BOLD, 'Noto Serif CJK JP')
    PROVENANCE.update({f'U+{cp:04X}': value for cp, value in gugyeol_descriptions.items()})
    notices = []
    for family, source in (('NotoSerifJP', jp), ('NotoSerifHentaigana', donor)):
        notice = (ROOT/'sources/upstream'/family/'OFL.txt').read_text().split('\n\n')[0]
        notices.append(notice)
        notices.extend(record.toUnicode() for record in source['name'].names if record.nameID == 0)
    with TTFont(CJK_SOURCE) as cjk:
        notices.extend(record.toUnicode() for record in cjk['name'].names if record.nameID == 0)
    notices = '\n'.join(dict.fromkeys(notices))
    notices += '\n' + (ROOT/'sources/upstream/FRBTaiwaneseKana/LICENSE.txt').read_text().split('\n\n')[0]
    for nid in (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,21,22,25):
        font['name'].removeNames(nameID=nid)
    for nid, value in {0:notices, 1:FAMILY, 2:style, 3:VERSION+';'+stem,
                       4:FAMILY+' '+style, 5:'Version '+VERSION, 6:stem,
                       16:FAMILY,17:style,
                       10:'Japanese text and historical kana derived from Noto Serif JP, Noto Serif Hentaigana and FRB Taiwanese Kana. Includes historical kana constructions, SQUARE PAATU, transcription symbols, Okinawan kana with documented private-use mappings, and a hooked WU stylistic alternate.',
                       13:'This Font Software is licensed under the SIL Open Font License, Version 1.1. See OFL.txt.',
                       14:'https://openfontlicense.org'}.items():
        font['name'].setName(value,nid,3,1,0x409)
    for nid, value in {1:FAMILY_JA, 2:style, 4:FAMILY_JA+' '+style,
                       16:FAMILY_JA, 17:style}.items():
        font['name'].setName(value,nid,3,1,0x411)
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].ulUnicodeRange2 |= 1 << 28  # Bit 60: BMP Private Use Area.
    font['OS/2'].achVendID = 'NONE'
    font['OS/2'].usWeightClass = 400 if weight == 400 else 700
    if weight == 400:
        font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~33) | 64
        font['head'].macStyle = 0
    else:
        font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~65) | 32
        font['head'].macStyle = 1
        font['OS/2'].panose.bWeight = 8  # PANOSE Bold.
    for tag in ('STAT','DSIG'):
        if tag in font: del font[tag]
    font.save(OUT/(stem+'.ttf'))
    font.flavor = 'woff2'
    font.save(OUT/(stem+'.woff2'))
    if weight != 400:
        _write_bold_record(stem, font, originals, points, retained, recipes, alternate, minnan_points, small_weight)
        bold_sheet(stem)
        print(f'Built {FAMILY} Bold {VERSION}: {len(font.getBestCmap()):,} encoded characters.')
        return
    licence = (ROOT/'sources/upstream/NotoSerifJP/OFL.txt').read_text().split('\n\n', 1)[1]
    (OUT/'OFL.txt').write_text(notices+'\n\n'+licence)
    (OUT/'NOTICE.txt').write_text(
        'GenZui Serif / 源萃明朝 (げんずい)\n\n'
        'Noto Serif JP: full Japanese base and historical-kana construction components.\n'
        'GenZui: twenty-one constructed forms using Noto kana components and original drawing.\n'
        'Noto Serif CJK JP: U+5344 (卄), converted to TrueType curves.\n'
        'https://github.com/notofonts/noto-cjk/tree/main/Serif\n'
        'GenZui: five ideographic tally marks and five ideographic-description symbols.\n'
        'GenZui: SQUARE PAATU uses native Noto Serif JP squared-katakana components.\n'
        'WU has a curved default and a hooked stylistic alternate (ss01).\n'
        'GenZui: 18 Funatsu Okinawan bases and eight raised katakana, drawn from Noto components.\n'
        'Private-use conventions follow Nishiki-teki and Xim Sans; see okinawan-mappings.json.\n'
        '181 구결자 (Korean gugyeol) at the Hanyang private-use convention (U+F67E-U+F77C),\n'
        "each drawn from the face's own glyph of its twin ideograph, or from Noto Serif CJK\n"
        'JP where the twin is absent from the face; see gugyeol-forms.json.\n'
        'Noto Serif Hentaigana: 290 historical forms, combining marks and small YE components.\n'
        'The Google, Adobe and Noto Project notices are retained in OFL.txt.\n'
        'https://github.com/google/fonts/tree/main/ofl/notoserifjp\n'
        'https://github.com/notofonts/hentaigana\n\n'
        'FRB Taiwanese Kana by Fredrick R. Brennan, SIL OFL 1.1:\n'
        '13 Minnan tone letters and U+0305/U+0323 combining marks.\n'
        'GenZui supplies kana attachment and contextual vertical tone placement.\n'
        'https://github.com/ctrlcctrlv/FRBTaiwaneseKana\n'
        'See FRB-OFL.txt and FRB-README.md.\n\n'
        'Jigmo2, 2025-09-12, by Koichi Kamichi and GlyphWiki contributors:\n'
        'Historical comparison fonts through 0.102 use its U+2CF02 outline.\n'
        'The current font replaces that outline with a GenZui drawing.\n'
        'The source outline is dedicated under CC0 1.0.\n'
        'See Jigmo-CC0.txt, Jigmo-README.txt and Jigmo-THANKS.txt.\n'
        'https://kamichikoichi.github.io/jigmo/\n\n'
        'The combined GenZui font is distributed under SIL OFL 1.1.\n'
        'The CC0 dedication of the original Jigmo material remains in effect.\n'
        'Upstream authors do not endorse this derivative.\n'
    )
    shutil.copyfile(CJK_SOURCE.parent/'OFL.txt', OUT/'NotoSerifCJK-OFL.txt')
    shutil.copyfile(ROOT/'sources/manifest.json', OUT/'source-manifest.json')
    shutil.copyfile(ROOT/'sources/Unicode-LICENSE.txt', OUT/'Unicode-LICENSE.txt')
    for source, dest in (('LICENSE.txt', 'Jigmo-CC0.txt'), ('README.txt', 'Jigmo-README.txt'),
                         ('THANKS.txt', 'Jigmo-THANKS.txt')):
        shutil.copyfile(ROOT/'sources/upstream/Jigmo'/source, OUT/dest)
    for source, dest in (('LICENSE.txt', 'FRB-OFL.txt'), ('README.md', 'FRB-README.md')):
        shutil.copyfile(ROOT/'sources/upstream/FRBTaiwaneseKana'/source, OUT/dest)
    (OUT/'sources.json').write_text(json.dumps({'family':FAMILY,'family_ja':FAMILY_JA,
        'reading':'げんずい','status':'development build','weight':400,
        'version':VERSION,'base':'Noto Serif JP','base_characters':len(originals),
        'encoded_characters':len(font.getBestCmap()),
        'target_characters':len(points),'retained_historical':retained,
        'provisional_forms':len(recipes), 'compatibility_forms':1,
        'okinawan_pua_characters':len(OKINAWAN_PUA),
        'gugyeol_pua_characters':len(GUGYEOL_PUA),
        'honkoku_forms':len(HONKOKU), 'honkoku_constructions':10,
        'stylistic_sets':{'ss01':{'name':'Hooked WU','codepoint':'U+1B11F',
            'default':'curved','alternate':'hooked','glyph':alternate}},
        'minnan_source_forms':len(minnan_points),
        'added':PROVENANCE,'small_vertical_offset':[140,190],
        'revised_forms':[f'U+{cp:04X}' for cp in REVISED],
        'revision_0103':[f'U+{cp:04X}' for cp in REVISION_0103],
        'revision_0104':[f'U+{cp:04X}' for cp in REVISION_0104],
        'revision_0107':[f'U+{cp:04X}' for cp in REVISION_0107],
        'revision_0108':[f'U+{cp:04X}' for cp in REVISION_0108],
        'revision_0109':[f'U+{cp:04X}' for cp in REVISION_0109],
        'revision_0110':[f'U+{cp:04X}' for cp in REVISION_0110],
        'alternate_revision_0110':['U+1B11F/ss01'],
        'revision_0112':[f'U+{cp:04X}' for cp in REVISION_0112],
        'revision_0115':[f'U+{cp:04X}' for cp in REVISION_0115],
        'revision_0117':[f'U+{cp:04X}' for cp in REVISION_0117],
        'revision_0111':[f'U+{cp:04X}' for cp in REVISION_0111],
        'alternate_revision_0111':['U+1B11F/ss01'],
        'alternate_revision_0109':['U+1B11F/ss01'],
        'alternate_revision_0108':['U+1B11F/ss01'],
        'alternate_revision_0107':['U+1B11F/ss01'],
        'revision_0106':[f'U+{cp:04X}' for cp in REVISION_0106],
        'revision_0105':[f'U+{cp:04X}' for cp in REVISION_0105],
        'source_kinds':{f'U+{cp:04X}':('gugyeol' if cp in GUGYEOL_PUA else
            'jp' if cp in originals else
            'cjk' if cp == 0x5344 else
            'genzui' if cp in OKINAWAN_PUA or cp in recipes or cp == PAATU or cp in HONKOKU else 'frb' if cp in minnan_points else
            'hentaigana') for cp in sorted(points | set(OKINAWAN_PUA) | set(GUGYEOL_PUA))}},ensure_ascii=False,indent=2)+'\n')
    for file in ('JP-Regular.ttf', 'JP-Regular.woff2', 'HKSerifProof-Regular.ttf',
                 'HKSerifProof-Regular.woff2', 'Hentaigana-Regular.ttf',
                 'checks.json', 'browser-checks.json'):
        (OUT/file).unlink(missing_ok=True)
    shutil.copyfile(ROOT/'data/okinawan/mappings.json', OUT/'okinawan-mappings.json')
    shutil.copyfile(ROOT/'data/gugyeol/forms.json', OUT/'gugyeol-forms.json')
    proof()
    print(f'Built {FAMILY} {VERSION}: {len(font.getBestCmap()):,} encoded characters, {len(points)} historical targets, {len(recipes)} provisional forms.')


def _write_bold_record(stem, font, originals, points, retained, recipes, alternate, minnan_points, small_weight):
    (OUT/'sources-bold.json').write_text(json.dumps({
        'family': FAMILY, 'family_ja': FAMILY_JA, 'reading': 'げんずい',
        'status': 'development build', 'weight': 700, 'style': 'Bold',
        'stem': stem, 'version': VERSION, 'base': 'Noto Serif JP',
        'base_characters': len(originals),
        'encoded_characters': len(font.getBestCmap()),
        'target_characters': len(points), 'retained_historical': retained,
        'provisional_forms': len(recipes),
        'small_source_weight': small_weight,
        'drawings': 'GenZui constructions take their native strokes from Noto Serif JP Bold. Each drawn stroke has its own Bold master, drawn to the stroke weight of the Bold kana.',
        'stylistic_sets': {'ss01': {'name': 'Hooked WU', 'glyph': alternate}},
        'minnan_source_forms': len(minnan_points),
        'added': PROVENANCE,
    }, ensure_ascii=False, indent=2) + '\n')


def bold_sheet(stem):
    """Contact sheet of the Bold face, with Regular above it when that file exists."""
    bold_path = OUT / (stem + '.ttf')
    regular_path = OUT / (STEM + '.ttf')
    rows = []
    if regular_path.exists():
        rows.append(('Regular', ImageFont.truetype(str(regular_path), 86)))
    rows.append(('Bold', ImageFont.truetype(str(bold_path), 86)))
    lines = [
        '源萃明朝の太字。漢字と仮名が同じ太さで並ぶ。',
        'あいうえおアイウエオトシ正んけ',
        ''.join(chr(cp) for cp in range(0x1B002, 0x1B012)),
        ''.join(chr(cp) for cp in REVISED),
        ''.join(chr(cp) for cp in SMALL),
        '卄' + ''.join(chr(cp) for cp in TALLIES) + '⿷⿺',
        ''.join(chr(cp) for cp in list(MINNAN_TONES)[:8]),
    ]
    label = ImageFont.truetype('DejaVuSans.ttf', 18)
    width, line_h, pad = 1680, 120, 16
    image = Image.new('RGB', (width, pad + len(rows) * len(lines) * line_h), '#f6f4ee')
    draw = ImageDraw.Draw(image)
    for r, (name, face) in enumerate(rows):
        for i, text in enumerate(lines):
            y = pad + (r * len(lines) + i) * line_h
            draw.text((pad, y), name, font=label, fill='#5c675f')
            draw.text((110, y), text, font=face, fill='#182620')
    image.save(OUT / 'bold-proof.png')
    css = (OUT / (stem + '.woff2')).read_bytes()
    import base64 as _b64
    data = _b64.b64encode(css).decode()
    samples = '<br>'.join(html.escape(line) for line in lines)
    (OUT / 'bold-proof.html').write_text(
        '<!doctype html><meta charset="utf-8"><title>GenZui Serif Bold</title>'
        f'<style>@font-face{{font-family:Bold;src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:700}}'
        'body{margin:32px;background:#f6f4ee;color:#182620;font:22px/1.7 Bold,serif}'
        f'h1{{font:18px/1.4 system-ui;font-weight:600}}</style><h1>GenZui Serif Bold {VERSION}</h1><p>{samples}</p>')


def proof():
    provenance = PROVENANCE or json.loads((OUT/'sources.json').read_text())['added']
    rows = []
    for item in repertoire():
        if item['codepoint'] not in provenance:
            continue
        ch = item['character']
        label = item.get('label', item['name'])
        source = ('FRB Taiwanese Kana · adapted layout' if ord(ch) in (*MINNAN_TONES, *MINNAN_MARKS) else
                  'GenZui / Noto components · provisional')
        picture, horizontal, vertical, marks = ch, f'あ{ch}い<br>ア{ch}イ', f'あ{ch}い', f'{ch}\u3099 {ch}\u309a'
        if ord(ch) in HONKOKU:
            source = 'Noto Serif CJK JP' if ord(ch) == 0x5344 else 'GenZui / Noto components'
            horizontal = vertical = ('廿卄卅' if ord(ch) == 0x5344 else
                ''.join(chr(cp) for cp in TALLIES) if ord(ch) in TALLIES else
                '⿷'+ch+'⿺')
            marks = ch
        elif ord(ch) == PAATU:
            horizontal = vertical = '㌫㌬㌭'
            marks = 'パーツ'
            source = 'GenZui / Noto squared-katakana components'
        elif ord(ch) in MINNAN_TONES:
            horizontal = vertical = f'チア{ch}'
            marks = f'チ\u0305\u0323ア{ch}'
        elif ord(ch) in MINNAN_MARKS:
            picture = f'チ{ch}'
            horizontal = vertical = f'ウ{ch}ゥ{ch}'
            marks = 'チ\u0305\u0323'
        rows.append(f'<tr><th>{item["codepoint"]}<small>{label}</small><small>{source}</small></th>'
                    f'<td class="glyph specimen">{picture}</td><td class="text specimen">{horizontal}</td>'
                    f'<td><div class="vertical text specimen">{vertical}</div></td>'
                    f'<td class="glyph specimen">{marks}</td></tr>')
    data = base64.b64encode((OUT/(STEM+'.woff2')).read_bytes()).decode()
    css = f'@font-face{{font-family:Proof;src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:400}}'
    page = (ROOT/'templates/serif-proof.html').read_text()
    replacements = {
        '{{CSS}}': css, '{{ROWS}}': ''.join(rows),
        '{{VERSION}}': VERSION,
        '{{OKINAWAN}}': '　'.join(''.join(chr(int(cp,16)) for cp in e['output']) for e in OKINAWAN_ENTRIES),
        '{{ALL}}': ''.join(chr(cp) for cp in range(0x1B001, 0x1B11F)),
        '{{LICENSE}}': html.escape((OUT/'OFL.txt').read_text()),
    }
    for token, value in replacements.items():
        page = page.replace(token, value)
    (OUT/'serif-proof.html').write_text(page)
    font = ImageFont.truetype(str(OUT/(STEM+'.ttf')), 130)
    label = ImageFont.truetype('DejaVuSans.ttf', 18)
    cps = sorted(int(k[2:], 16) for k in provenance)
    image = Image.new('RGB', (1200, ((len(cps)+5)//6)*265), '#f7f5ef')
    draw = ImageDraw.Draw(image)
    for i, cp in enumerate(cps):
        x, y = (i % 6)*200, (i // 6)*265
        draw.text((x+18, y+16), f'U+{cp:04X}', font=label, fill='#28322e')
        draw.text((x+28, y+45), chr(cp), font=font, fill='#182620')
    image.save(OUT/'serif-proof.png')


if __name__ == '__main__':
    build()
