"""Validate GenZui Sans P against GenZui Sans: baked palt widths and unchanged vertical ink."""
import hashlib
import io
import json

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from sans import BOLD_STEM, OUT, STEM, VERSION
from sans_p import (BOLD_STEM_P, DESCRIPTION, FAMILY_P, FAMILY_P_JA, STEM_P, kern_pairs, palt_adjustments,
                    subtables)

JAPANESE = ('日本語の文章、「かっこ」（丸）［角］【隅】。ゔぁぃぅぇぉっゃゅょ ガギグゲゴ パピプペポ ヴァ ー〜…・'
            'ＡＢＣ１２３ａｂｃ！？：；～＋＝（）｛｝ｱｲｳｴｵﾊﾞﾊﾟ¥￥$％'
            '゙゚がぱガパ'
            'いろはにほへと ちりぬるを わかよたれそ つねならむ アイウエオ カキクケコ')
MARKED = 'かがきぎはばぱカガハバパヴゔ'


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
    if language:
        buffer.language = language
    if script:
        buffer.script = script
    hb.shape(font, buffer, features)
    return [(info.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for info, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def ink(font, shaped):
    """Ink box of each shaped glyph in line coordinates, None for empty glyphs."""
    result, x, y = [], 0, 0
    for gid, ax, ay, dx, dy in shaped:
        g = font['glyf'][font.getGlyphName(gid)]
        result.append((x+dx+g.xMin, y+dy+g.yMin, x+dx+g.xMax, y+dy+g.yMax) if g.numberOfContours else None)
        x, y = x+ax, y+ay
    return result, (x, y)


def outline(font, name):
    return font['glyf'][name].getCoordinates(font['glyf'])


def check_face(source_stem, stem, bold):
    style = 'Bold' if bold else 'Regular'
    source_path, path = OUT/(source_stem+'.ttf'), OUT/(stem+'.ttf')
    source_data, data = source_path.read_bytes(), path.read_bytes()
    base, font = TTFont(source_path), TTFont(path)
    web = TTFont(OUT/(stem+'.woff2'))
    web.flavor = None
    web_data = serialized(web)
    base_engine, engine, web_engine = shaper(source_data), shaper(data), shaper(web_data)
    deltas, facts = palt_adjustments(base)
    assert deltas and not any(font['GPOS'].table.FeatureList.FeatureRecord[i].FeatureTag in ('palt', 'halt')
                              for i in range(font['GPOS'].table.FeatureList.FeatureCount))
    order, cmap = base.getGlyphOrder(), base.getBestCmap()
    assert font.getGlyphOrder() == web.getGlyphOrder() == order
    assert font.getBestCmap() == web.getBestCmap() == cmap
    assert [t.uvsDict for t in font['cmap'].tables if t.format == 14] == [
        t.uvsDict for t in base['cmap'].tables if t.format == 14]

    # Outlines and metrics: palt glyphs move and widen, every other glyph is identical.
    for name in order:
        dx, da = deltas.get(name, (0, 0))
        old, new = outline(base, name), outline(font, name)
        assert outline(web, name) == new and font['hmtx'][name] == web['hmtx'][name], name
        assert font['vmtx'][name] == base['vmtx'][name] == web['vmtx'][name], name
        if name not in deltas:
            assert new == old and font['hmtx'][name] == base['hmtx'][name], name
            continue
        assert [(x+dx, y) for x, y in old[0]] == list(new[0]) and old[1:] == new[1:], name
        advance, lsb = base['hmtx'][name]
        assert font['hmtx'][name] == (advance+da, font['glyf'][name].xMin if font['glyf'][name].numberOfContours else 0)
        assert advance+da >= 0
    for table in ('GSUB', 'GDEF', 'BASE'):
        assert base[table].compile(base) == font[table].compile(font), table
    for field in ('ascent', 'descent', 'lineGap'):
        assert getattr(font['hhea'], field) == getattr(base['hhea'], field), field
    for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent', 'usWeightClass',
                  'fsSelection'):
        assert getattr(font['OS/2'], field) == getattr(base['OS/2'], field), field

    # GPOS: only palt and halt are gone, and vert gained the compensation lookup.
    def tags(f):
        return sorted({r.FeatureTag for r in f['GPOS'].table.FeatureList.FeatureRecord})
    assert tags(font) == [t for t in tags(base) if t not in ('palt', 'halt')]
    assert vert_lookups(font) == [n+1 for n in vert_lookups(base)]

    # Shaping. Characters that palt adjusts, alone and between neighbours, then running text.
    affected = sorted(cp for cp, name in cmap.items() if name in deltas)
    texts = [chr(cp) for cp in affected] + [f'あ{chr(cp)}い' for cp in affected] + [f'ア{chr(cp)}ア' for cp in affected]
    texts += [JAPANESE, ''.join(chr(cp) for cp in affected),
              ''.join(chr(cp) for cp in sorted(cmap) if cp < 0x3400 and cmap[cp] not in deltas)[:600],
              ''.join(c+m for c in MARKED for m in ('゙', '゚'))]
    pairs = []
    for index in kern_pairs(base, set(deltas))['lookups']:
        for kind, sub in subtables(base['GPOS'].table.LookupList.Lookup[index]):
            if sub.Format == 1:
                reverse = {n: cp for cp, n in cmap.items()}
                for first, records in zip(sub.Coverage.glyphs, sub.PairSet):
                    for record in records.PairValueRecord:
                        if first in reverse and record.SecondGlyph in reverse:
                            pairs.append(chr(reverse[first])+chr(reverse[record.SecondGlyph]))
    texts += pairs
    cases = {'horizontal': 0, 'vertical': 0, 'features': 0}
    for text in texts:
        for script in (None, 'Hira', 'Kana', 'Hani'):
            for language in ('ja', None):
                expected = shape(base_engine, text, 'ltr', {'palt': True}, script, language)
                actual = shape(engine, text, 'ltr', None, script, language)
                assert [g[:3] for g in actual] == [g[:3] for g in expected] and \
                    [g[4] for g in actual] == [g[4] for g in expected], (text[:20], script, language)
                assert ink(font, actual) == ink(base, expected), (text[:20], script, language)
                assert actual == shape(web_engine, text, 'ltr', None, script, language)
                cases['horizontal'] += 1
        assert ink(font, shape(engine, text, 'ltr'))[0] == ink(base, shape(base_engine, text, 'ltr', {'palt': True}))[0]
        # Features that no longer exist have no effect.
        for features in ({'palt': True}, {'halt': True}, {'palt': False}):
            assert shape(engine, text, 'ltr', features) == shape(engine, text, 'ltr'), features
            cases['features'] += 1
        for direction_features in (None, {'vkrn': True, 'vpal': True}, {'vhal': True}):
            expected = shape(base_engine, text, 'ttb', direction_features)
            actual = shape(engine, text, 'ttb', direction_features)
            assert [g[0] for g in actual] == [g[0] for g in expected] and \
                [g[2] for g in actual] == [g[2] for g in expected], (text[:20], direction_features)
            assert ink(font, actual) == ink(base, expected), (text[:20], direction_features)
            assert actual == shape(web_engine, text, 'ttb', direction_features)
            cases['vertical'] += 1
    # Text the font does not adjust shapes identically with and without palt.
    plain = ''.join(c for c in 'AVATAR office 0123456789 日本語の漢字' if cmap[ord(c)] not in deltas)
    assert len(plain) > 20
    for direction in ('ltr', 'ttb'):
        assert shape(engine, plain, direction) == shape(base_engine, plain, direction)

    for nid in (1, 16):
        assert font['name'].getName(nid, 3, 1, 0x409).toUnicode() == FAMILY_P
        assert font['name'].getName(nid, 3, 1, 0x411).toUnicode() == FAMILY_P_JA
    assert font['name'].getName(4, 3, 1, 0x409).toUnicode() == FAMILY_P+' '+style
    assert font['name'].getName(4, 3, 1, 0x411).toUnicode() == FAMILY_P_JA+' '+style
    for nid in (2, 17):
        assert font['name'].getName(nid, 3, 1, 0x409).toUnicode() == style
    assert font['name'].getDebugName(3) == VERSION+';'+stem
    assert font['name'].getDebugName(5) == 'Version '+VERSION and font['name'].getDebugName(6) == stem
    assert font['name'].getDebugName(10) == DESCRIPTION
    assert font['name'].getDebugName(0) == base['name'].getDebugName(0)
    assert bool(font['OS/2'].fsSelection & 32) == bool(font['head'].macStyle & 1) == bold
    return {
        'style': style, 'ttf_sha256': hashlib.sha256(data).hexdigest(),
        'woff2_sha256': hashlib.sha256((OUT/(stem+'.woff2')).read_bytes()).hexdigest(),
        'base_ttf_sha256': hashlib.sha256(source_data).hexdigest(),
        'palt_glyphs': len(deltas), 'palt_glyphs_with_cmap_entry': len(affected),
        'identical_glyphs_and_metrics': len(order)-len(deltas), 'encoded_characters': len(cmap),
        'palt_lookups': facts['lookups'], 'palt_subtables': facts['subtables'],
        'shaping_cases': cases, 'kern_pairs_tested': len(pairs), 'woff2_matches_ttf': True,
    }


def vert_lookups(font):
    """Lookup count of each GPOS vert feature record."""
    return [len(r.Feature.LookupListIndex) for r in font['GPOS'].table.FeatureList.FeatureRecord
            if r.FeatureTag == 'vert']


def check():
    report = {'status': 'passed', 'family': FAMILY_P, 'family_ja': FAMILY_P_JA, 'version': VERSION,
              'regular': check_face(STEM, STEM_P, False), 'bold': check_face(BOLD_STEM, BOLD_STEM_P, True)}
    for key, prefix in (('regular', ''), ('bold', 'bold_')):
        for ext in ('ttf', 'woff2'):
            report[prefix+ext+'_sha256'] = report[key][ext+'_sha256']
    (OUT/'checks-p.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    check()
