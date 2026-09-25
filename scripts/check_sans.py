"""Validate Sans outlines, the JP base, encoded coverage and shaping."""
import base64
import hashlib
import io
import json
import re

import uharfbuzz as hb
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.ttLib import TTFont
from statistics import median

from sans import DRAWN, FAMILY, FAMILY_JA, OUT, REGULAR_WEIGHT, STEM, VERSION, instance, sources
from sans_forms import REFITS, WI_LOWER_RISE, WI_UPPER_DROP
from serif import contours
import pathops
from repertoire import repertoire, MINNAN_MARKS, MINNAN_TONES
from honkoku import HONKOKU
from check_coverage import check_coverage


def serialized(font):
    stream = io.BytesIO()
    font.save(stream)
    return stream.getvalue()


def shaper(data):
    font = hb.Font(hb.Face(data))
    font.scale = (1000, 1000)
    return font


def shape(font, text, direction='ltr', features=None, script=None, language='ja'):
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.direction, buffer.language = direction, language
    if script:
        buffer.script = script
    hb.shape(font, buffer, features)
    return [(info.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for info, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def stem(font, points):
    """Median stroke width estimate: twice the filled area over the perimeter."""
    glyphs, cmap, widths = font.getGlyphSet(), font.getBestCmap(), []
    for cp in points:
        area, perimeter = AreaPen(glyphs), PerimeterPen(glyphs)
        glyphs[cmap[cp]].draw(area)
        glyphs[cmap[cp]].draw(perimeter)
        widths.append(2*abs(area.value)/perimeter.value)
    return round(median(widths), 1)


def boxes(font, shaped):
    result, x, y = [], 0, 0
    for gid, ax, ay, dx, dy in shaped:
        g = font['glyf'][font.getGlyphName(gid)]
        result.append((x+dx+g.xMin, y+dy+g.yMin, x+dx+g.xMax, y+dy+g.yMax))
        x, y = x+ax, y+ay
    return result


def check(weight=400):
    face = sources(weight)
    stem_name, style, bold, refits = face['stem'], face['style'], weight == 700, REFITS[weight]
    path = OUT/(stem_name+'.ttf')
    data = path.read_bytes()
    font, engine = TTFont(path), shaper(data)
    web = TTFont(OUT/(stem_name+'.woff2'))
    web.flavor = None
    web_engine = shaper(serialized(web))
    base_data = serialized(instance('NotoSansJP', weight))
    base, base_engine = TTFont(io.BytesIO(base_data)), shaper(base_data)
    cmap, base_cmap = font.getBestCmap(), base.getBestCmap()
    targets = {ord(item['character']) for item in repertoire()}
    assert set(cmap) == set(base_cmap) | targets
    assert len(cmap) == 17070
    assert not any(0xE000 <= cp <= 0xF8FF or cp >= 0xF0000 for cp in cmap)
    assert web.getBestCmap() == cmap
    assert font.getGlyphOrder() == web.getGlyphOrder()
    assert font.getGlyphOrder()[:len(base.getGlyphOrder())] == base.getGlyphOrder()
    for cp, name in base_cmap.items():
        assert cmap[cp] == name, hex(cp)
    for name in base.getGlyphOrder():
        assert font['glyf'][name].getCoordinates(font['glyf']) == base['glyf'][name].getCoordinates(base['glyf']), name
        for table in ('hmtx', 'vmtx'):
            assert font[table][name] == base[table][name], (name, table)
    for name in font.getGlyphOrder():
        assert font['glyf'][name].getCoordinates(font['glyf']) == web['glyf'][name].getCoordinates(web['glyf']), name
        for table in ('hmtx', 'vmtx'):
            assert font[table][name] == web[table][name], (name, table)
    assert [t.uvsDict for t in font['cmap'].tables if t.format == 14] == [
        t.uvsDict for t in base['cmap'].tables if t.format == 14]
    for field in ('ascent', 'descent', 'lineGap'):
        assert getattr(font['hhea'], field) == getattr(base['hhea'], field), field
    for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap'):
        assert getattr(font['OS/2'], field) == getattr(base['OS/2'], field), field
    samples = [''.join(chr(cp) for cp in sorted(base_cmap)),
               '「日本語」、かな・カナ。がぱヴか\u3099は\u309aカ\u3099ハ\u309a',
               'あゟい・アヿイ・ぁぃっゃァィッャー〜（）［］…！？',
               'AVATAR office affine 0123456789 1/2 カナ ABC あいうえお']
    variants = ''.join(chr(cp)+chr(selector) for t in base['cmap'].tables if t.format == 14
                       for selector, pairs in t.uvsDict.items() for cp, _ in pairs)
    if variants:
        samples.append(variants)
    base_cases = 0
    for text in samples:
        for direction in ('ltr', 'ttb'):
            for features in (None, {'palt': True}, {'pwid': True}, {'hwid': True},
                             {'jp78': True}, {'ruby': True}, {'vpal': True, 'vkrn': True}):
                actual = shape(engine, text, direction, features)
                assert actual == shape(base_engine, text, direction, features), (text[:30], direction, features)
                assert actual == shape(web_engine, text, direction, features)
                base_cases += 1

    donor, text_instance = TTFont(face['archaic']), TTFont(face['text'])
    genseki = TTFont(face['genseki'])
    donor_cmap, gen_cmap = donor.getBestCmap(), genseki.getBestCmap()
    if not bold:
        assert donor['OS/2'].usWeightClass == 500 and text_instance['OS/2'].usWeightClass == 400
    retained = {'noto_archaic': 0, 'noto_text': 0, 'genseki': 0, 'genseki_refit': 0}
    mark_cases = 0
    for cp in sorted(targets - set(base_cmap)):
        name = cmap[cp]
        g = font['glyf'][name]
        assert g.numberOfContours != 0, hex(cp)
        source = (None if cp in DRAWN else (donor if cp in REGULAR_WEIGHT else text_instance) if cp in donor_cmap
                  else genseki if cp in gen_cmap else None)
        if source and cp in refits:
            old = gen_cmap[cp]
            spec, s = refits[cp], refits[cp]['scale']
            o = genseki['glyf'][old]
            expected = ((o.xMax-o.xMin)*s, (o.yMax-o.yMin)*s)
            # Erosion trims each side by the stated amount; the body grows by the scale.
            assert abs((g.xMax-g.xMin) - expected[0] + 2*spec['erode']) <= 3, hex(cp)
            assert abs((g.yMax-g.yMin) - expected[1] + 2*spec['erode']) <= 3, hex(cp)
            assert abs((g.yMin+g.yMax)/2 - (o.yMin+o.yMax)/2 - spec['shift'][1]) <= 2, hex(cp)
            assert font['hmtx'][name] == (1000, g.xMin) and font['vmtx'][name] == (1000, 880-g.yMax)
            retained['genseki_refit'] += 1
        elif source:
            old = source.getBestCmap()[cp]
            assert g.getCoordinates(font['glyf']) == source['glyf'][old].getCoordinates(source['glyf']), hex(cp)
            assert font['hmtx'][name] == source['hmtx'][old], hex(cp)
            retained['noto_archaic' if source is donor else 'noto_text' if source is text_instance else 'genseki'] += 1
        if cp in (*MINNAN_TONES, *MINNAN_MARKS):
            continue
        for direction in ('ltr', 'ttb'):
            shaped = shape(engine, chr(cp), direction)
            assert len(shaped) == 1 and shaped[0][0], hex(cp)
            assert shaped[0][1:3] == ((1000, 0) if direction == 'ltr' else (0, -1000)), hex(cp)
            assert shaped == shape(web_engine, chr(cp), direction)
            if cp == 0x332C or cp in HONKOKU:
                continue
            for mark in ('\u3099', '\u309a'):
                text = chr(cp)+mark
                actual = shape(engine, text, direction)
                assert len(actual) == 2 and all(g[0] for g in actual), (hex(cp), direction)
                assert actual[1][1:3] == (0, 0), (hex(cp), direction)
                b, m = boxes(font, actual)
                if direction == 'ltr':
                    assert m[1] >= b[3]+18, (hex(cp), direction, b, m)
                    assert 0 <= m[0] < m[2] <= 1000, (hex(cp), m)
                    assert m[3] <= font['OS/2'].usWinAscent
                else:
                    assert m[0] >= b[2]+18, (hex(cp), direction, b, m)
                for script in ('Latn', 'Zzzz', 'Hira', 'Kana', 'Hani'):
                    assert actual == shape(engine, text, direction, script=script), (hex(cp), script)
                assert actual == shape(web_engine, text, direction)
                mark_cases += 1
    assert retained == {'noto_archaic': 4, 'noto_text': 286, 'genseki': 17, 'genseki_refit': 3}, retained
    # Alternate WI spans the height of WI, its bars keep WI's width, and its
    # metrics follow the other historical kana.
    wi, drawn = font['glyf'][cmap[ord('ヰ')]], font['glyf'][cmap[0x1B128]]
    assert abs(drawn.yMax - wi.yMax) <= 12 and abs(drawn.yMin - wi.yMin) <= 12, (drawn.yMin, drawn.yMax)
    wi_outline = pathops.Path()
    font.getGlyphSet()[cmap[0x1B128]].draw(wi_outline.getPen())
    for index, shift in ((2, WI_LOWER_RISE), (3, -WI_UPPER_DROP)):
        pen = pathops.Path()
        contours(font, ord('ヰ'), [index]).replay(pen.getPen())
        x0, y0, x1, y1 = pen.bounds
        y = (y0 + y1) / 2 + shift
        band = pathops.Path(); b = band.getPen()
        b.moveTo((-100, y-1)); b.lineTo((1100, y-1)); b.lineTo((1100, y+1)); b.lineTo((-100, y+1)); b.closePath()
        cut = pathops.op(wi_outline, band, pathops.PathOp.INTERSECTION).bounds
        assert abs(cut[0] - x0) <= 1 and abs(cut[2] - x1) <= 1, (index, cut, (x0, x1))
    assert font['hmtx'][cmap[0x1B128]] == (1000, drawn.xMin) and font['vmtx'][cmap[0x1B128]] == (1000, 880-drawn.yMax)
    # The hentaigana's median stem matches the hiragana's, and the archaic kana
    # the katakana's, within two units.
    stems = {label: stem(font, cps) for label, cps in (
        ('hiragana', [ord(c) for c in 'いろはにほへとちりぬるをわかよたれそつねならむうゐのおくやまけふこえてあさきゆめみしゑひもせす']),
        ('hentaigana', range(0x1B002, 0x1B11F)),
        ('katakana', [ord(c) for c in 'イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス']),
        ('archaic', sorted(REGULAR_WEIGHT)))}
    assert abs(stems['hiragana'] - stems['hentaigana']) <= 2, stems
    assert abs(stems['katakana'] - stems['archaic']) <= 2, stems
    # KOTO's body falls within the heights of TOKI, TOTE and TOMO; alternate NE
    # reaches the katakana cap height; the small archaic YE sits with small kana.
    heights = {cp: font['glyf'][cmap[cp]].yMax - font['glyf'][cmap[cp]].yMin
               for cp in (0x1B123, 0x1B124, 0x1B125, 0x2A708)}
    peers = [heights[cp] for cp in (0x1B124, 0x1B125, 0x2A708)]
    assert min(peers) <= heights[0x1B123] <= max(peers), heights
    assert font['glyf'][cmap[0x1B127]].yMax >= font['glyf'][cmap[ord('ア')]].yMax - 1
    assert -60 <= font['glyf'][cmap[0x1B168]].yMin <= -20
    assert 'ss01' not in {r.FeatureTag for r in font['GSUB'].table.FeatureList.FeatureRecord}
    for direction in ('ltr', 'ttb'):
        assert shape(engine, '𛄟', direction) == shape(engine, '𛄟', direction, {'ss01': True})
        for text in ('𛄤\u3099か\u3099', '𛅨\u309aハ\u309a'):
            assert shape(engine, text, direction)[-1:] == shape(base_engine, text[-2:], direction)

    minnan_cases = 0
    for ch in 'チウオァィゥェォャュョ':
        for direction in ('ltr', 'ttb'):
            for suffix in ('\u0305', '\u0323', '\u0305\u0323', '\u0323\u0305'):
                actual = shape(engine, ch+suffix, direction)
                assert actual[0] == shape(engine, ch, direction)[0]
                assert all(g[0] and g[1:3] == (0, 0) for g in actual[1:])
                bounds = boxes(font, actual)
                for m in bounds[1:]:
                    assert m[1] >= bounds[0][3]+35 or m[3] <= bounds[0][1]-30
                assert actual == shape(web_engine, ch+suffix, direction)
                minnan_cases += 1
    for cp in MINNAN_TONES:
        for text in ('チ', 'チア', 'チァム', 'チァムア'):
            for features in (None, {'vkrn': False}, {'ruby': True}):
                actual = shape(engine, text+chr(cp), 'ttb', features)
                assert actual[:-1] == shape(engine, text, 'ttb', features)
                assert actual[-1][1:3] == (0, 0)
                bounds = boxes(font, actual)
                assert bounds[-1][0] >= max(b[2] for b in bounds[:-1])+20, (text, hex(cp), bounds)
                assert -len(text)*1000 <= bounds[-1][1] < bounds[-1][3] <= 0
                assert actual == shape(web_engine, text+chr(cp), 'ttb', features)
                minnan_cases += 1

    for nid in (1, 16):
        assert font['name'].getName(nid, 3, 1, 0x409).toUnicode() == FAMILY
        assert font['name'].getName(nid, 3, 1, 0x411).toUnicode() == FAMILY_JA
    for nid in (2, 17):
        assert font['name'].getName(nid, 3, 1, 0x409).toUnicode() == style
    assert font['name'].getDebugName(6) == stem_name
    assert font['name'].getDebugName(5) == 'Version '+VERSION
    assert font['OS/2'].usWeightClass == weight and 'fvar' not in font and 'STAT' not in font
    assert bool(font['OS/2'].fsSelection & 32) == bool(font['head'].macStyle & 1) == bold
    for source in (base, donor, genseki):
        for record in source['name'].names:
            if record.nameID == 0:
                assert record.toUnicode() in (OUT/'OFL.txt').read_text()
                assert record.toUnicode() in font['name'].getDebugName(0)
    if not bold:
        text = (OUT/'index.html').read_text(encoding='utf-8')
        embedded = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', text)
        assert len(embedded) == 1 and base64.b64decode(embedded[0]) == (OUT/(STEM+'.woff2')).read_bytes()
        assert '/home/' not in text and 'GenZui Serif' not in text
    coverage = check_coverage(path, OUT/('kana-coverage-bold.json' if bold else 'kana-coverage.json'))
    report = {
        'status': 'passed', 'family': FAMILY, 'family_ja': FAMILY_JA, 'style': style, 'version': VERSION,
        'ttf_sha256': hashlib.sha256(data).hexdigest(),
        'woff2_sha256': hashlib.sha256((OUT/(stem_name+'.woff2')).read_bytes()).hexdigest(),
        'encoded_characters': len(cmap), 'unchanged_jp_characters': len(base_cmap),
        'unchanged_jp_glyphs_and_metrics': len(base.getGlyphOrder()),
        'jp_shaping_cases': base_cases, 'noto_hentaigana_outlines': retained, 'median_stems': stems,
        'refits': {f'U+{cp:04X}': spec['reason'] for cp, spec in refits.items()},
        'mark_cases': mark_cases, 'minnan_cases': minnan_cases, 'kana_coverage': coverage['coverage'],
        'woff2_matches_ttf': True,
    }
    (OUT/('checks-bold.json' if bold else 'checks.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'kana_coverage'}, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    check()
