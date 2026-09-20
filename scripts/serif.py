"""Build the first static serif extension proof from pinned Noto outlines."""
import base64
import copy
import html
import json

from fontTools import subset
from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont
import pathops

from repertoire import font_path, repertoire
from sources import ROOT, verify

OUT = ROOT / 'build/serif'
FAMILY = 'HK Serif Proof'
SMALL = {0x1B132: 0x3053, 0x1B150: 0x3090, 0x1B151: 0x3091,
         0x1B152: 0x3092, 0x1B155: 0x30B3, 0x1B164: 0x30F0,
         0x1B165: 0x30F1, 0x1B166: 0x30F2, 0x1B167: 0x30F3,
         0x1B168: 0x1B121}
PROVENANCE = {}


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


def fit(outline, box):
    bounds = BoundsPen(None)
    outline.replay(bounds)
    x0, y0, x1, y1 = bounds.bounds
    a, b, c, d = box
    sx, sy = (c-a)/(x1-x0), (d-b)/(y1-y0)
    return transform(outline, (sx, 0, 0, sy, a-sx*x0, b-sy*y0))


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


def layout(font, vertical, points):
    cmap = font.getBestCmap()
    marks = {}
    for cp in (0x3099, 0x309A):
        name = cmap[cp]
        vname = add(font, name+'.vert', copy.deepcopy(font['glyf'][name]))
        font['hmtx'][vname] = font['hmtx'][name]
        vertical[name] = vname
        marks[name] = (0, buildAnchor(0, 0))
        marks[vname] = (1, buildAnchor(0, 0))
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    sub = otTables.SingleSubst()
    sub.mapping = vertical
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    add_feature(font, 'GSUB', 'vert', lookup)
    add_feature(font, 'GSUB', 'vrt2', copy.deepcopy(lookup))
    bases = ({cmap[cp] for cp in points} | set(vertical.values())) - set(marks)
    anchors = {}
    for name in bases:
        g = font['glyf'][name]
        # Keep both marks clear of the top outline and within the em's width.
        anchors[name] = {0: buildAnchor(830, g.yMax - 626),
                         1: buildAnchor(g.xMax + 148, 0)}
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildMarkBasePosSubtable(marks, anchors, font.getReverseGlyphMap())]
    lookup.SubTableCount = 1
    add_feature(font, 'GPOS', 'mark', lookup)
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    classes.update({name: 1 for name in bases})
    classes.update({name: 3 for name in marks})
    font['vhea'] = newTable('vhea')
    v = font['vhea']
    v.tableVersion, v.ascent, v.descent, v.lineGap = 0x00010000, 500, -500, 0
    v.advanceHeightMax, v.minTopSideBearing, v.minBottomSideBearing = 1000, 0, 0
    v.yMaxExtent = 1000
    v.caretSlopeRise, v.caretSlopeRun, v.caretOffset = 0, 1, 0
    v.reserved1 = v.reserved2 = v.reserved3 = v.reserved4 = 0
    v.metricDataFormat, v.numberOfVMetrics = 0, len(font.getGlyphOrder())
    font['vmtx'] = newTable('vmtx')
    font['vmtx'].metrics = {
        name: (0 if name in marks else 1000, 880 - getattr(font['glyf'][name], 'yMax', 0))
        for name in font.getGlyphOrder()
    }
    # Includes the highest positioned mark; Windows must not clip it.
    top = max(font['glyf'][name].yMax + 252 for name in bases)
    font['OS/2'].usWinAscent = max(font['OS/2'].usWinAscent, top)


def build():
    verify()
    OUT.mkdir(parents=True, exist_ok=True)
    jp_points = set(range(0x3041, 0x3100)) | {0x5B50, 0x4E95}
    jp = instance('NotoSerifJP', 400, jp_points)
    heavier = instance('NotoSerifJP', 500, set(SMALL.values()) - {0x1B121})
    h_heavier = instance('NotoSerifHentaigana', 500, {0x1B121})
    font = instance('NotoSerifHentaigana', 400)
    original = font.getBestCmap()
    originals = set(original)
    def part(ch, indices=None):
        return contours(jp, ord(ch), indices)
    stem = part('ト', [0])
    connector = RecordingPen()
    parse_path('M230 770 C330 704 530 755 661 767 C715 776 730 734 677 719 '
               'C532 683 452 619 453 555 C454 511 474 481 496 460 L470 440 '
               'C409 493 393 554 424 609 C464 677 554 704 599 721 '
               'C437 698 296 691 230 770 Z', connector)
    recipes = {
        0x1B11F: [part('け', [0, 1]), transform(part('け', [2]), (1,0,0,1,0,-65)), part('ほ', [3])],
        0x1B123: [part('と', [0]), connector],
        0x1B124: [fit(stem, (135,-40,275,760)), fit(part('キ'), (270,-40,905,760))],
        0x1B125: [fit(stem, (135,-40,275,760)), fit(part('テ'), (235,-40,905,760))],
        0x1B126: [fit(part('ヨ'), (95,-30,550,705)), fit(stem, (615,70,710,680)), fit(stem, (795,-40,895,760))],
        0x1B127: [fit(part('子'), (125,-40,875,760))],
        0x1B128: [fit(part('井'), (125,-40,875,760))],
        0x309F: [part('ゟ')], 0x30FF: [part('ヿ')],
    }
    descriptions = {
        0x1B11F: 'Noto Serif JP KE strokes with the upper bar from HO; loop-free WU construction.',
        0x1B123: 'Noto Serif JP TO bowl with a newly drawn upper KOTO curve.',
        0x1B124: 'Noto Serif JP TO stem beside KI.',
        0x1B125: 'Noto Serif JP TO stem beside TE.',
        0x1B126: 'Noto Serif JP YO with two upright stems derived from TO.',
        0x1B127: 'Noto Serif JP U+5B50 fitted to the kana body.',
        0x1B128: 'Noto Serif JP U+4E95 fitted to the kana body.',
        0x309F: 'Noto Serif JP U+309F, unchanged outline.',
        0x30FF: 'Noto Serif JP U+30FF, unchanged outline.',
    }
    vertical = {}
    for cp, source_cp in SMALL.items():
        source = h_heavier if cp == 0x1B168 else heavier
        # Weight 500 before scaling gives small forms more substance than a
        # literal reduction of Regular; positioning follows JP small kana.
        recipes[cp] = [transform(contours(source, source_cp), (.72,0,0,.72,140,-25))]
        descriptions[cp] = f'Noto Serif {"Hentaigana" if cp == 0x1B168 else "JP"} U+{source_cp:04X}, weight 500, scale 0.72.'
    cmap_add = {}
    for cp, parts in sorted(recipes.items()):
        name = f'u{cp:05X}'
        add(font, name, glyph(parts))
        cmap_add[cp] = name
        if cp in SMALL:
            vertical[name] = add(font, name+'.vert', glyph([transform(p, (1,0,0,1,140,190)) for p in parts]))
        PROVENANCE[f'U+{cp:04X}'] = descriptions[cp]
    for table in font['cmap'].tables:
        if table.isUnicode() and table.format != 14:
            table.cmap.update({cp: name for cp, name in cmap_add.items() if cp <= (0xFFFF if table.format == 4 else 0x10FFFF)})
    points = {ord(item['character']) for item in repertoire()}
    layout(font, vertical, points)
    for nid in (1,2,3,4,5,6,16,17,18,21,22,25):
        font['name'].removeNames(nameID=nid)
    for nid, value in {1:FAMILY, 2:'Regular', 3:'0.001;HKSerifProof-Regular',
                       4:FAMILY+' Regular', 5:'Version 0.001', 6:'HKSerifProof-Regular',
                       16:FAMILY,17:'Regular',
                       10:'Outline proof derived from Noto Serif Hentaigana and Noto Serif JP. New forms require typographic review.'}.items():
        font['name'].setName(value,nid,3,1,0x409)
    notices = '\n'.join((ROOT/'sources/upstream'/family/'OFL.txt').read_text().split('\n\n')[0]
                        for family in ('NotoSerifJP','NotoSerifHentaigana'))
    font['name'].setName(notices,0,3,1,0x409)
    font['head'].fontRevision = 0.001
    font['OS/2'].usWeightClass = 400
    font['OS/2'].fsSelection = (font['OS/2'].fsSelection & ~33) | 64
    font['head'].macStyle = 0
    for tag in ('STAT','DSIG'):
        if tag in font: del font[tag]
    font.save(OUT/'HKSerifProof-Regular.ttf')
    font.flavor = 'woff2'
    font.save(OUT/'HKSerifProof-Regular.woff2')
    jp.save(OUT/'JP-Regular.ttf')
    jp.flavor = 'woff2'
    jp.save(OUT/'JP-Regular.woff2')
    (OUT/'sources.json').write_text(json.dumps({'status':'outline proof','weight':400,
        'target_characters':len(points),'retained_historical':len(points & originals),
        'added':PROVENANCE,'small_vertical_offset':[140,190]},ensure_ascii=False,indent=2)+'\n')
    proof()
    print('Built Regular serif proof: 309 target characters, 19 additions (17 gaps and two existing JP digraphs).')


def proof():
    rows = []
    for item in repertoire():
        if item['codepoint'] not in PROVENANCE: continue
        ch = item['character']
        rows.append(f'<tr><th>{item["codepoint"]}<small>{item["name"]}</small></th>'
                    f'<td class="glyph">{ch}</td><td class="text">あ{ch}い<br>ア{ch}イ</td>'
                    f'<td class="vertical text">あ{ch}い</td><td class="glyph">{ch}\u3099 {ch}\u309a</td></tr>')
    fonts = {name:base64.b64encode((OUT/file).read_bytes()).decode()
             for name,file in [('Proof','HKSerifProof-Regular.woff2'),('Context','JP-Regular.woff2')]}
    css = ''.join(f'@font-face{{font-family:{name};src:url(data:font/woff2;base64,{data}) format("woff2")}}'
                  for name,data in fonts.items())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Serif kana extension — first outline proof</title><style>{{CSS}}
*{box-sizing:border-box}body{margin:0;background:#f7f5ef;color:#28322e;font:16px/1.6 system-ui,sans-serif}main{max-width:1250px;margin:auto;padding:30px}h1{font-size:30px;line-height:1.2}h2{font-size:21px;margin-top:32px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:18px;border:1px solid #ccd1c8}th{width:25%;text-align:left;font-size:14px}small{display:block;font-size:11px}.glyph{font:64px/1.8 Proof}.text{font:38px/1.8 Context,Proof}.vertical{writing-mode:vertical-rl;min-height:190px}.grid{font:36px/1.9 Proof;overflow-wrap:anywhere;letter-spacing:4px}a{color:#215d46}label{display:block;margin:20px 0}.scroll{overflow:auto}details{margin-top:24px}pre{white-space:pre-wrap;font-size:12px}.note{padding:15px;background:#e7ece3;border-left:3px solid #5d7553}
</style><main><h1>Serif kana extension</h1><p>Regular · first outline proof · Unicode 18</p>
<p>All 309 target characters are encoded: 286 hentaigana and 23 other historical kana. Noto Serif Hentaigana supplies 290 forms. The 19 additions below include 17 missing forms and the two existing Noto Serif JP digraphs.</p>
<p class="note">The new forms are provisional. Inspect their joins, proportions and stroke weight beside modern kana. “HK Serif Proof” is a temporary font-menu identifier. The project family name is undecided.</p>
<p><a href="HKSerifProof-Regular.ttf">Installable Regular TTF</a> · <a href="HKSerifProof-Regular.woff2">Webfont</a> · <a href="sources.json">Outline provenance</a></p>
<label>Preview size <input id="size" type="range" min="24" max="96" value="64"> <output id="value">64 px</output></label>
<div class="scroll"><table lang="ja"><thead><tr><th>Character</th><th>Outline</th><th>Horizontal</th><th>Vertical</th><th>Mark positioning</th></tr></thead><tbody>{{ROWS}}</tbody></table></div>
<p>Mark samples exercise positioning; they do not imply that every combination is linguistically used. Small kana have separate positions for vertical text. New outlines use Noto components; no outline data was extracted from Unicode charts.</p>
<h2>All 286 hentaigana</h2><p class="grid" lang="ja">{{ALL}}</p>
<h2>Licences</h2>{{LICENSES}}</main><script>document.querySelector('#size').addEventListener('input',event=>{document.querySelectorAll('.glyph').forEach(el=>el.style.fontSize=event.target.value+'px');document.querySelector('#value').textContent=event.target.value+' px'});</script></html>'''
    licenses = ''.join('<details><summary>'+family+'</summary><pre>'+html.escape((ROOT/'sources/upstream'/family/'OFL.txt').read_text())+'</pre></details>' for family in ('NotoSerifJP','NotoSerifHentaigana'))
    page = page.replace('{{ROWS}}',''.join(rows)).replace('{{ALL}}',''.join(chr(cp) for cp in range(0x1B001,0x1B11F))).replace('{{LICENSES}}',licenses).replace('{{CSS}}',css)
    (OUT/'serif-proof.html').write_text(page)
    font = ImageFont.truetype(str(OUT/'HKSerifProof-Regular.ttf'),130)
    label = ImageFont.truetype('DejaVuSans.ttf',18)
    cps = [int(k[2:],16) for k in PROVENANCE if int(k[2:],16)>0xFFFF]
    image = Image.new('RGB',(1200,850),'#f7f5ef')
    draw = ImageDraw.Draw(image)
    for i, cp in enumerate(cps):
        x,y=(i%6)*200,(i//6)*265
        draw.text((x+18,y+16),f'U+{cp:04X}',font=label,fill='#28322e')
        draw.text((x+28,y+45),chr(cp),font=font,fill='#182620')
    image.save(OUT/'serif-proof.png')


if __name__ == '__main__':
    build()
