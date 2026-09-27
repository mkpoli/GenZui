"""Build equal-size source comparisons for both Okinawan font weights."""
import json
import hashlib
import re
import pathops
from fontTools.pens.recordingPen import RecordingPen

from fontTools import subset
from fontTools.ttLib import TTFont

from okinawan_ligatures import source
from okinawan import DAKUTEN, ENTRIES, voiced_parts
from serif import OUT as FONT_OUT, VERSION, glyph, contours, transform
from sources import ROOT

OUT = ROOT / 'build/okinawan-release'
VARIANTS = ('A', 'B')
NEIGHBOURS = {'TU': 'とつ', 'TI': 'てい', 'KWA': 'くわ', 'KWI': 'くい',
              'KWE': 'くえ', 'HWA': 'ふわ', 'HWI': 'ふい', 'HWE': 'ふえ',
              'WU': 'をう', 'TSI': 'つい'}


def composed_name(font, cp):
    cmap = font.getBestCmap()
    names = {lig.LigGlyph
             for lookup in font['GSUB'].table.LookupList.Lookup if lookup.LookupType == 4
             for sub in lookup.SubTable
             for lig in sub.ligatures.get(cmap[cp], [])
             if lig.Component == [cmap[0x3099]]}
    assert len(names) == 1, hex(cp)
    return names.pop()


def webfont(style, variant):
    font = TTFont(FONT_OUT / f'GenZuiSerif-{style}.ttf', recalcTimestamp=False)
    if variant == 'A':
        from okinawan_bold import drawings
        cmap = font.getBestCmap()
        for cp, parts in drawings(font, contours, option="A", style=style).items():
            merged = pathops.Path()
            for part in parts:
                shape = pathops.Path()
                part.replay(shape.getPen())
                merged = pathops.op(merged, shape, pathops.PathOp.UNION)
            pen = RecordingPen()
            merged.draw(pen)
            g = glyph([pen])
            name = cmap[cp]
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880-g.yMax)
    if variant == 'A':
        for cp in DAKUTEN:
            if cp == 0xF467:
                continue  # SI/ZI are confirmed in both options.
            name = composed_name(font, cp)
            parts = voiced_parts(font, cp, [contours(font, cp)], contours, transform,
                                 mark_scale=1.0)
            g = glyph(parts)
            font['glyf'][name] = g
            g.recalcBounds(font['glyf'])
            font['hmtx'][name] = (1000, g.xMin)
            font['vmtx'][name] = (1000, 880 - g.yMax)
    points = {int(g['codepoint'], 16) for g in source()['glyphs']} | set(DAKUTEN)
    points.update(range(0x3041, 0x30A0))
    options = subset.Options()
    options.recalc_timestamp = False
    sub = subset.Subsetter(options=options)
    sub.populate(unicodes=points)
    sub.subset(font)
    font.flavor = 'woff2'
    font.save(OUT / f'{style.lower()}-{variant}.woff2')


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for style in ('Regular', 'Bold'):
        for variant in VARIANTS:
            webfont(style, variant)
    fonts = {s: TTFont(FONT_OUT / f'GenZuiSerif-{s}.ttf') for s in ('Regular','Bold')}
    voices = {int(e['output'][0],16): dict(label=e['label'], character=''.join(chr(int(c,16)) for c in e['output']), reference=DAKUTEN[int(e['output'][0],16)][0]) for e in ENTRIES if len(e['output'])==2 and int(e['output'][0],16) in DAKUTEN}
    glyphs = []
    entries = [dict(label=g['label'], character=chr(int(g['codepoint'],16)), neighbours=NEIGHBOURS[g['label']]) for g in source()['glyphs']]
    entries.append(dict(label='SI',character=chr(0xF467),neighbours='すず'))
    for g in entries:
        cp = ord(g['character'])
        if cp in voices:
            g['voiced'] = voices[cp]
        g['tops'] = {}
        for style,f in fonts.items():
            top = lambda ch: f['glyf'][f.getBestCmap()[ord(ch)]].yMax
            g['tops'][style] = dict(plain=top(g['neighbours'][0]),voiced=top(voices[cp]['reference']) if cp in voices else 0)
        glyphs.append(g)
    data = dict(version=VERSION, glyphs=glyphs, history=json.loads((ROOT/'data/okinawan/tu-wu-history.json').read_text())['designs'])
    template = (ROOT / 'templates/okinawan-release/index.html').read_text()
    def font_url(match):
        file = OUT / match[1]
        suffix = '?v=' + hashlib.sha256(file.read_bytes()).hexdigest()[:12] if file.exists() else ''
        return 'url(' + match[1] + suffix + ')'
    template = re.sub(r'url\(([^()]+\.woff2)\)', font_url, template)
    (OUT / 'index.html').write_text(template.replace('{{DATA}}', json.dumps(data, ensure_ascii=False)))
    # Remove superseded comparison fonts.
    for name in ('regular.woff2', 'bold-C.woff2', 'bold-A-700.woff2', 'bold-B-700.woff2', 'regular-before.woff2', 'regular-A-alt.woff2', 'regular-B-alt.woff2', 'bold-A-alt.woff2', 'bold-B-alt.woff2', 'bold-before.woff2'):
        (OUT / name).unlink(missing_ok=True)
    print(f'Okinawan {VERSION}: equal-size source context, per-weight choices and voiced pairs.')


if __name__ == '__main__':
    build()
