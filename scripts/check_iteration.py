"""Check the kana proportions against the immutable 0.111 release."""
import hashlib
import json
from fontTools.ttLib import TTFont
from check_refinements import mask, components
from serif_forms import REVISION_0112, wu_alternate
from sources import ROOT


def check_iteration(path, font):
    baseline = ROOT/'releases/v0.111/GenZuiSerif-Regular.ttf'
    expected = json.loads((ROOT/'research/baselines/gallery-0.111.json').read_text())
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == expected['full_ttf_sha256']
    before = TTFont(baseline)
    cmap = font.getBestCmap()
    assert cmap == before.getBestCmap()
    assert font.getGlyphOrder() == before.getGlyphOrder()
    changed = []
    names = {cmap[cp] for cp in REVISION_0112}
    for name in font.getGlyphOrder():
        old = before['glyf'][name].getCoordinates(before['glyf'])
        new = font['glyf'][name].getCoordinates(font['glyf'])
        if old != new:
            changed.append(name)
        if name not in names:
            assert font['hmtx'][name] == before['hmtx'][name], name
            assert font['vmtx'][name] == before['vmtx'][name], name
    assert set(changed) == names, changed
    assert wu_alternate(font) not in changed

    def bounds(face, cp):
        g = face['glyf'][face.getBestCmap()[cp]]
        return [g.xMin, g.yMin, g.xMax, g.yMax]

    tomo = bounds(font, 0x2A708)
    tote = bounds(font, 0x1B125)
    toki = bounds(font, 0x1B124)
    # TOTE should match TOMO's width; TOKI should occupy slightly less space.
    assert abs((tote[2]-tote[0])-(tomo[2]-tomo[0])) <= 4, (tote, tomo)
    assert toki[2]-toki[0] < tomo[2]-tomo[0]
    assert toki[3]-toki[1] < tomo[3]-tomo[1] < tote[3]-tote[1]
    assert abs(tote[3]-tomo[3]) <= 2
    ratios = {}
    for cp in REVISION_0112:
        name = cmap[cp]
        old = bounds(before, cp); new = bounds(font, cp)
        ratios[f'U+{cp:X}'] = (new[2]-new[0])/(old[2]-old[0])
        assert new[0] > old[0] and new[1] > old[1]
        assert new[2] < old[2] and new[3] < old[3]
        assert font['hmtx'][name][0] == before['hmtx'][name][0] == 1000
        assert font['vmtx'][name][0] == before['vmtx'][name][0] == 1000
        assert font['vmtx'][name][1]+new[3] == before['vmtx'][name][1]+old[3]
    assert ratios['U+1B124'] < ratios['U+1B125'] < 1

    joins = []
    for cp, expected_components in [(0x1B124, 1), (0x1B125, 2), (0x2A708, 1)]:
        for size in (24, 32, 40, 48, 64, 128):
            actual = components(mask(path, cp, size))
            assert actual == expected_components, (hex(cp), size, actual)
            joins.append({'codepoint':f'U+{cp:X}', 'size_px':size, 'components':actual})
    return {'baseline':'0.111',
            'changed_outlines':[f'U+{cp:X}' for cp in REVISION_0112],
            'unchanged_glyphs':len(font.getGlyphOrder())-len(changed),
            'all_other_outlines_and_metrics_unchanged':True,
            'wu_variants_unchanged':True,
            'fullwidth_advances_and_vertical_origins_preserved':True,
            'width_ratios':ratios,
            'bounds':{'TOMO':tomo, 'TOTE':tote, 'TOKI':toki},
            'reading_size_connectivity':joins, 'status':'passed'}
