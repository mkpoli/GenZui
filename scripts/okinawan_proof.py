"""Build the local Okinawan type comparison from the current font.

Optional reference fonts are read from a local directory. They are only copied
into the ignored study output; they are not packaged with GenZui or its site.
"""
import argparse
import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from okinawan import ENTRIES
from okinawan_drawings import BASES, RAISED
from sources import ROOT

OUT = ROOT/'build/okinawan'

# Glyph order of the EUDC font embedded in Funatsu's chart PDF, by entry id.
CHART_GLYPHS = {'tu': 1, 'du': 2, 'ti': 3, 'di': 4, 'kwa': 5, 'gwa': 6, 'kwi': 7, 'gwi': 8,
                'kwe': 9, 'gwe': 10, 'hwa': 11, 'hwi': 12, 'hwe': 13, "'ya": 14, "'yu": 15,
                "'yo": 16, "'wa": 17, "'wi": 18, "'we": 19, "'n": 20, 'yi': 21, 'wu': 22,
                'ye': 23, 'si': 25, 'zi': 26, 'tsi': 27, 'dzi': 28}


def chart_font(pdf, target):
    """Map the chart's embedded Funatsu glyphs to the entries' code points."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['mutool', 'extract', str(pdf.resolve())], cwd=tmp, check=True, capture_output=True)
        fonts = [TTFont(f) for f in Path(tmp).glob('*.ttf')]
        font = next(f for f in fonts if f['head'].unitsPerEm == 256)
        drawn = [n for n in font.getGlyphOrder() if font['glyf'][n].numberOfContours > 0]
        table = CmapSubtable.newSubtable(4)
        table.platformID, table.platEncID, table.language = 3, 1, 0
        table.cmap = {int((e.get('legacy') or e['output'])[0], 16): drawn[CHART_GLYPHS[e['id']]]
                      for e in ENTRIES if e['id'] in CHART_GLYPHS}
        cmap = newTable('cmap'); cmap.tableVersion, cmap.tables = 0, [table]
        font['cmap'] = cmap
        # Browsers refuse a font without the tables the PDF embedding dropped.
        for tag in ('post', 'OS/2', 'name'):
            if tag not in font:
                font[tag] = newTable(tag)
        post = font['post']; post.formatType = 3.0
        for attr in ('italicAngle', 'underlinePosition', 'underlineThickness', 'isFixedPitch',
                     'minMemType42', 'maxMemType42', 'minMemType1', 'maxMemType1'):
            setattr(post, attr, 0)
        os2 = font['OS/2']
        for attr, value in dict(version=4, xAvgCharWidth=256, usWeightClass=400, usWidthClass=5, fsType=0,
                ySubscriptXSize=0, ySubscriptYSize=0, ySubscriptXOffset=0, ySubscriptYOffset=0,
                ySuperscriptXSize=0, ySuperscriptYSize=0, ySuperscriptXOffset=0, ySuperscriptYOffset=0,
                yStrikeoutSize=0, yStrikeoutPosition=0, sFamilyClass=0, ulUnicodeRange1=0, ulUnicodeRange2=0,
                ulUnicodeRange3=0, ulUnicodeRange4=0, achVendID='NONE', fsSelection=64, usFirstCharIndex=0xE000,
                usLastCharIndex=0xF8FF, sTypoAscender=220, sTypoDescender=-36, sTypoLineGap=0, usWinAscent=220,
                usWinDescent=36, ulCodePageRange1=0, ulCodePageRange2=0, sxHeight=0, sCapHeight=0,
                usDefaultChar=0, usBreakChar=32, usMaxContext=0).items():
            setattr(os2, attr, value)
        from fontTools.ttLib.tables.O_S_2f_2 import Panose
        os2.panose = Panose()
        name = font['name']; name.names = []
        for nid, text in ((1, 'Funatsu chart'), (2, 'Regular'), (3, 'Funatsu chart'), (4, 'Funatsu chart'), (6, 'FunatsuChart')):
            name.setName(text, nid, 3, 1, 0x409)
        font.flavor = 'woff2'; font.save(target)
        return sorted(table.cmap)


def build(reference_dir=None):
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = OUT/'fonts'; fonts.mkdir(exist_ok=True)
    home = OUT/'home'
    if not home.exists() and not home.is_symlink():
        home.symlink_to(Path('../site'), target_is_directory=True)
    shutil.copyfile(ROOT/'build/serif/GenZuiSerif-Regular.woff2', fonts/'genzui.woff2')
    shutil.copyfile(ROOT/'releases/v0.114/GenZuiSerif-Regular.woff2', fonts/'previous.woff2')
    references = {}
    if reference_dir:
        for key, filename in [('fk', 'FK-Okinawa-reference.ttf'),
                              ('nishiki', 'nishiki-teki.ttf'),
                              ('mgen', 'mgenkanaplus.woff2'),
                              ('xim', 'Xim-Sans-Handwritten.ttf')]:
            source = reference_dir/filename
            if not source.is_file():
                continue
            font = TTFont(source, recalcTimestamp=False)
            covered = set(font.getBestCmap())
            points = set(range(0xF450, 0xF46B)) | {int(e['output'][0], 16) for e in ENTRIES}
            options = subset.Options(); options.recalc_timestamp = False
            sub = subset.Subsetter(options=options); sub.populate(unicodes=points & covered); sub.subset(font)
            font.flavor = 'woff2'; font.save(fonts/(key+'.woff2'))
            references[key] = sorted(points & covered)
        chart = reference_dir/'funatsu-chart.pdf'
        if chart.is_file():
            references['chart'] = chart_font(chart, fonts/'chart.woff2')
        image = reference_dir/'frokinawa-sample.jpg'
        if image.is_file():shutil.copyfile(image, OUT/'frokinawa-sample.jpg')
    groups = {'funatsu': [], 'prefecture': []}
    for entry in ENTRIES:
        text = ''.join(chr(int(cp,16)) for cp in entry['output'])
        label = entry['label'] if entry['system']=='funatsu' else entry['label'].replace('Raised ', '')
        first = int(entry['output'][0], 16)
        if entry['system'] == 'funatsu':
            # The ordinary kana the letter joins or modifies, set in the same face.
            plain = entry.get('kana') or BASES.get(first) or chr(first)
        else:
            plain = chr(RAISED[first][0])
        groups[entry['system']].append(
            f'<article class="letter" data-id="{html.escape(entry["id"],quote=True)}">'
            f'<header><strong>{html.escape(label)}</strong><span>{html.escape(entry.get("kana") or "")}</span></header>'
            '<div class="pair">'
            f'<div><span class="glyph new" lang="ryu">{text}</span><small>GenZui</small></div>'
            '<div><span class="glyph reference" lang="ryu"></span><small class="reference-label"></small></div>'
            f'<div><span class="glyph new plain" lang="ja">{plain}</span><small>Ordinary kana</small></div>'
            '</div>'
            f'<p class="codes">{" + ".join("U+"+cp for cp in entry["output"])}</p></article>')
    page = (ROOT/'templates/okinawan.html').read_text()
    if not (OUT/'frokinawa-sample.jpg').is_file():
        start = page.index('<figure>')
        end = page.index('</figure>', start) + len('</figure>')
        page = page[:start] + page[end:]
    for key, value in {'{{FUNATSU}}': ''.join(groups['funatsu']),
                       '{{RAISED}}': ''.join(groups['prefecture']),
                       '{{DATA}}': json.dumps({'entries':ENTRIES,'references':references},ensure_ascii=False).replace('<','\\u003c')}.items():
        page=page.replace(key,value)
    (OUT/'index.html').write_text(page)
    print(f'Okinawan comparison: {len(ENTRIES)} forms; {len(references)} reference fonts.')
    return OUT


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--references',type=Path)
    build(parser.parse_args().references)
