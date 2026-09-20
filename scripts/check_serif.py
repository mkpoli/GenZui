"""Check the full JP base, historical outlines, marks and vertical layout."""
import base64
import hashlib
import io
import json
import re

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from serif import FAMILY, OUT, SMALL, instance
from repertoire import repertoire


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
    buffer.direction = direction
    buffer.language = language
    if script:
        buffer.script = script
    hb.shape(font, buffer, features)
    return [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def boxes(font, shaped):
    positions, x, y = [], 0, 0
    for gid, ax, ay, dx, dy in shaped:
        glyph = font['glyf'][font.getGlyphName(gid)]
        positions.append((x+dx+glyph.xMin, y+dy+glyph.yMin,
                          x+dx+glyph.xMax, y+dy+glyph.yMax))
        x += ax
        y += ay
    return positions


def check():
    path = OUT/'HKSerifProof-Regular.ttf'
    data = path.read_bytes()
    font, engine = TTFont(path), shaper(data)
    cmap, chars = font.getBestCmap(), repertoire()
    # Serialization rounds instantiated coordinates exactly as in the build.
    jp_data = serialized(instance('NotoSerifJP', 400))
    jp, jp_engine = TTFont(io.BytesIO(jp_data)), shaper(jp_data)
    original = TTFont(io.BytesIO(serialized(instance('NotoSerifHentaigana', 400))))
    source_cmap, jp_cmap = original.getBestCmap(), jp.getBestCmap()

    assert len(cmap) == 17033
    assert set(cmap) == set(jp_cmap) | {ord(item['character']) for item in chars}
    assert all(cmap[cp] == name for cp, name in jp_cmap.items())
    assert font.getGlyphOrder()[:len(jp.getGlyphOrder())] == jp.getGlyphOrder()
    for name in jp.getGlyphOrder():
        assert (font['glyf'][name].getCoordinates(font['glyf']) ==
                jp['glyf'][name].getCoordinates(jp['glyf'])), name
        assert font['hmtx'][name] == jp['hmtx'][name], name
        assert font['vmtx'][name] == jp['vmtx'][name], name
    assert [t.uvsDict for t in font['cmap'].tables if t.format == 14] == [
        t.uvsDict for t in jp['cmap'].tables if t.format == 14]
    for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap',
                  'usWinAscent', 'usWinDescent', 'fsSelection'):
        assert getattr(font['OS/2'], field) == getattr(jp['OS/2'], field), field
    for field in ('ascent', 'descent', 'lineGap'):
        assert getattr(font['hhea'], field) == getattr(jp['hhea'], field), field

    # Exercise the complete base plus common punctuation, composition and
    # spacing features. Glyph IDs remain comparable because JP order is kept.
    samples = [
        ''.join(chr(cp) for cp in sorted(jp_cmap)),
        '「日本語」、かな・カナ。がぱヴか\u3099は\u309aカ\u3099ハ\u309a',
        'あゟい・アヿイ・ぁぃっゃァィッャー〜（）［］…！？',
        'AVATAR office affine 0123456789 1/2 カナ ABC あいうえお',
    ]
    variants = ''.join(chr(cp)+chr(selector)
                       for t in jp['cmap'].tables if t.format == 14
                       for selector, pairs in t.uvsDict.items() for cp, _ in pairs)
    if variants:
        samples.append(variants)
    jp_cases = 0
    for text in samples:
        for direction in ('ltr', 'ttb'):
            for features in (None, {'palt': True}, {'pwid': True},
                             {'hwid': True}, {'jp78': True}, {'ruby': True},
                             {'vpal': True, 'vkrn': True}):
                assert shape(engine, text, direction, features) == shape(
                    jp_engine, text, direction, features), (text[:30], direction, features)
                jp_cases += 1

    retained, marks_tested = 0, 0
    for item in chars:
        ch, cp = item['character'], ord(item['character'])
        name, glyph = cmap[cp], font['glyf'][cmap[cp]]
        assert glyph.numberOfContours != 0, name
        if cp in source_cmap:
            old_name = source_cmap[cp]
            assert glyph.getCoordinates(font['glyf']) == original['glyf'][old_name].getCoordinates(original['glyf']), name
            assert font['hmtx'][name] == original['hmtx'][old_name], name
            retained += 1
        horizontal, vertical = shape(engine, ch), shape(engine, ch, 'ttb')
        assert len(horizontal) == len(vertical) == 1, name
        assert horizontal[0][:3] == (font.getGlyphID(name), 1000, 0), name
        assert vertical[0][1:3] == (0, -1000), name
        if cp in SMALL:
            assert vertical[0][0] != horizontal[0][0], name
            vg = font['glyf'][font.getGlyphName(vertical[0][0])]
            assert vg.xMin == glyph.xMin+140 and vg.yMin == glyph.yMin+190, name
        for mark in ('\u3099', '\u309a'):
            for direction in ('ltr', 'ttb'):
                shaped = shape(engine, ch+mark, direction)
                if cp in jp_cmap:
                    assert shaped == shape(jp_engine, ch+mark, direction), name
                    continue
                # Latin/unknown script runs model engines that predate the
                # Unicode assignment of a historical base.
                for script in ('Latn', 'Zzzz', 'Hira', 'Kana'):
                    assert shape(engine, ch+mark, direction, script=script) == shaped, (name, script)
                assert len(shaped) == 2 and all(v[0] for v in shaped), (name, direction)
                assert shaped[1][1:3] == (0, 0), (name, direction)
                assert sum(v[1] for v in shaped) == (1000 if direction == 'ltr' else 0)
                assert sum(v[2] for v in shaped) == (-1000 if direction == 'ttb' else 0)
                base_box, mark_box = boxes(font, shaped)
                if direction == 'ltr':
                    assert mark_box[1] >= base_box[3]+18, (name, direction, base_box, mark_box)
                    assert 0 <= mark_box[0] < mark_box[2] <= 1000, (name, direction, mark_box)
                    assert mark_box[3] <= font['OS/2'].usWinAscent
                else:
                    assert mark_box[0] >= base_box[2]+18, (name, direction, base_box, mark_box)
                    assert mark_box[3] <= 0, (name, direction, mark_box)
                marks_tested += 1

    # A historical mark must not change how the following modern syllable shapes.
    for text in ('𛄤\u3099か\u3099', '𛅨\u309aハ\u309a'):
        for direction in ('ltr', 'ttb'):
            mixed = shape(engine, text, direction)
            assert mixed[-1:] == shape(jp_engine, text[-2:], direction), (text, direction)

    web = TTFont(OUT/'HKSerifProof-Regular.woff2')
    web.flavor = None
    web_engine = shaper(serialized(web))
    assert web.getBestCmap() == cmap
    for direction in ('ltr', 'ttb'):
        for text in samples + [''.join(item['character']+mark for item in chars)
                               for mark in ('\u3099', '\u309a')]:
            assert shape(engine, text, direction) == shape(web_engine, text, direction)
    assert font['name'].getDebugName(1) == FAMILY
    assert font['OS/2'].usWeightClass == 400
    assert 'fvar' not in font
    licence = (OUT/'OFL.txt').read_text()
    for source in (jp, original):
        for record in source['name'].names:
            if record.nameID == 0:
                assert record.toUnicode() in licence
                assert record.toUnicode() in font['name'].getDebugName(0)
    page = (OUT/'serif-proof.html').read_text()
    assert '/home/' not in page
    embedded = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', page)
    assert len(embedded) == 1
    assert base64.b64decode(embedded[0]) == (OUT/'HKSerifProof-Regular.woff2').read_bytes()
    assert page.count('<tr>') == 18 and 'LETTER SMALL KO' in page
    assert retained == 290 and len(chars) == 309
    report = {
        'font_version': font['name'].getDebugName(5),
        'ttf_sha256': hashlib.sha256(data).hexdigest(),
        'woff2_sha256': hashlib.sha256((OUT/'HKSerifProof-Regular.woff2').read_bytes()).hexdigest(),
        'encoded_characters': len(cmap), 'unchanged_jp_characters': len(jp_cmap),
        'unchanged_jp_glyphs_and_metrics': len(jp.getGlyphOrder()),
        'jp_shaping_regression_cases': jp_cases, 'jp_variation_sequences_preserved': True,
        'target_characters': len(chars), 'unchanged_historical_outlines': retained,
        'new_unicode18': sum(item['age'] == '18.0' for item in chars),
        'small_vertical_alternates': len(SMALL), 'mark_shaping_cases': marks_tested,
        'woff2_matches_ttf': True, 'single_embedded_font': True,
        'copyright_notices_preserved': True, 'status': 'passed',
    }
    (OUT/'checks.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    check()
