"""Validate Sans outlines, the JP base, encoded coverage and shaping."""
import base64
import hashlib
import io
import json
import re

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from sans import FAMILY, FAMILY_JA, OUT, REGULAR_WEIGHT, STEM, VERSION, instance
from sans_forms import REFITS
from sans_sources import DONOR, GENSEKI, LIGHT
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


def boxes(font, shaped):
    result, x, y = [], 0, 0
    for gid, ax, ay, dx, dy in shaped:
        g = font['glyf'][font.getGlyphName(gid)]
        result.append((x+dx+g.xMin, y+dy+g.yMin, x+dx+g.xMax, y+dy+g.yMax))
        x, y = x+ax, y+ay
    return result


def check():
    path = OUT/(STEM+'.ttf')
    data = path.read_bytes()
    font, engine = TTFont(path), shaper(data)
    web = TTFont(OUT/(STEM+'.woff2'))
    web.flavor = None
    web_engine = shaper(serialized(web))
    base_data = serialized(instance('NotoSansJP', 400))
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

    donor, light = TTFont(DONOR), TTFont(LIGHT)
    genseki = TTFont(GENSEKI/'GenSekiHentaiganaGothic.ttf')
    donor_cmap, gen_cmap = donor.getBestCmap(), genseki.getBestCmap()
    assert donor['OS/2'].usWeightClass == 500 and light['OS/2'].usWeightClass == 400
    retained = {'noto_regular': 0, 'noto_demilight': 0, 'genseki': 0, 'genseki_refit': 0}
    mark_cases = 0
    for cp in sorted(targets - set(base_cmap)):
        name = cmap[cp]
        g = font['glyf'][name]
        assert g.numberOfContours != 0, hex(cp)
        source = ((donor if cp in REGULAR_WEIGHT else light) if cp in donor_cmap
                  else genseki if cp in gen_cmap else None)
        if source and cp in REFITS:
            old = gen_cmap[cp]
            spec, s = REFITS[cp], REFITS[cp]['scale']
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
            retained['noto_regular' if source is donor else 'noto_demilight' if source is light else 'genseki'] += 1
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
    assert retained == {'noto_regular': 4, 'noto_demilight': 286, 'genseki': 18, 'genseki_refit': 3}, retained
    # KOTO, TOKI, TOTE and TOMO share a body height; the small archaic YE sits with small kana.
    heights = {cp: font['glyf'][cmap[cp]].yMax - font['glyf'][cmap[cp]].yMin
               for cp in (0x1B123, 0x1B124, 0x1B125, 0x2A708)}
    assert max(heights.values()) - min(heights.values()) <= 40, heights
    assert font['glyf'][cmap[0x1B127]].yMax >= 725
    assert -60 <= font['glyf'][cmap[0x1B168]].yMin <= -20
    for direction in ('ltr', 'ttb'):
        default = shape(engine, '𛄟', direction)
        hooked = shape(engine, '𛄟', direction, {'ss01': True})
        assert default != hooked and default[0][1:] == hooked[0][1:]
        assert hooked == shape(web_engine, '𛄟', direction, {'ss01': True})
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
    assert font['name'].getDebugName(6) == STEM
    assert font['name'].getDebugName(5) == 'Version '+VERSION
    assert font['OS/2'].usWeightClass == 400 and 'fvar' not in font and 'STAT' not in font
    for source in (base, donor, genseki):
        for record in source['name'].names:
            if record.nameID == 0:
                assert record.toUnicode() in (OUT/'OFL.txt').read_text()
                assert record.toUnicode() in font['name'].getDebugName(0)
    text = (OUT/'index.html').read_text()
    embedded = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', text)
    assert len(embedded) == 1 and base64.b64decode(embedded[0]) == (OUT/(STEM+'.woff2')).read_bytes()
    assert '/home/' not in text and 'GenZui Serif' not in text
    coverage = check_coverage(path, OUT/'kana-coverage.json')
    report = {
        'status': 'passed', 'family': FAMILY, 'family_ja': FAMILY_JA, 'version': VERSION,
        'ttf_sha256': hashlib.sha256(data).hexdigest(),
        'woff2_sha256': hashlib.sha256((OUT/(STEM+'.woff2')).read_bytes()).hexdigest(),
        'encoded_characters': len(cmap), 'unchanged_jp_characters': len(base_cmap),
        'unchanged_jp_glyphs_and_metrics': len(base.getGlyphOrder()),
        'jp_shaping_cases': base_cases, 'noto_hentaigana_outlines': retained,
        'refits': {f'U+{cp:04X}': spec['reason'] for cp, spec in REFITS.items()},
        'mark_cases': mark_cases, 'minnan_cases': minnan_cases, 'kana_coverage': coverage['coverage'],
        'woff2_matches_ttf': True,
    }
    (OUT/'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'kana_coverage'}, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    check()
