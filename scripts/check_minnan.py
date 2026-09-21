"""Check usable Minnan syllables, source fidelity and the archaic WU joins."""
from fontTools.pens.boundsPen import BoundsPen

from check_refinements import components, mask
from minnan import source_font
from repertoire import MINNAN_MARKS, MINNAN_TONES


def check_minnan(path, font, engine, shape, boxes):
    cmap = font.getBestCmap()
    donor = source_font()
    glyphs = donor.getGlyphSet()
    for cp in (*MINNAN_TONES, *MINNAN_MARKS):
        pen = BoundsPen(glyphs)
        glyphs[donor.getBestCmap()[cp]].draw(pen)
        g = font['glyf'][cmap[cp]]
        assert all(abs(a-b) <= 1 for a, b in zip(
            pen.bounds, (g.xMin, g.yMin, g.xMax, g.yMax))), hex(cp)
        assert font['hmtx'][cmap[cp]][0] == (0 if cp in MINNAN_MARKS else 500)

    mark_cases = 0
    # The Unicode description calls out full and small U/O; CHI and the other
    # small vowels exercise the context and both canonical orders of marks.
    for base in 'チウオァィゥェォャュョ':
        for direction in ('ltr', 'ttb'):
            for suffix in ('\u0305', '\u0323', '\u0305\u0323', '\u0323\u0305'):
                result = shape(engine, base+suffix, direction)
                assert all(g[0] for g in result)
                assert all(g[1:3] == (0, 0) for g in result[1:])
                assert result[0] == shape(engine, base, direction)[0]
                bounds = boxes(font, result)
                b = bounds[0]
                for mark in bounds[1:]:
                    assert mark[1] >= b[3]+35 or mark[3] <= b[1]-30, (base, suffix, direction, bounds)
                    assert abs((mark[0]+mark[2])-(b[0]+b[2])) <= 4
                mark_cases += 1
            assert shape(engine, base+'\u0305\u0323', direction) == shape(
                engine, base+'\u0323\u0305', direction)
            full_bar = boxes(font, shape(engine, 'ウ\u0305', direction))[1]
            small_bar = boxes(font, shape(engine, 'ゥ\u0305', direction))[1]
            assert .70 <= (small_bar[2]-small_bar[0])/(full_bar[2]-full_bar[0]) <= .74
            assert full_bar[3]-full_bar[1] == small_bar[3]-small_bar[1]

    tone_cases = 0
    for cp in MINNAN_TONES:
        tone = chr(cp)
        assert shape(engine, tone)[0][1:3] == (500, 0)
        assert shape(engine, tone, 'ttb')[0][1:3] == (0, -1000)
        for base in ('チ', 'チア', 'チァム', 'チァムア', 'チ\u0305\u0323ア'):
            count = sum(ch not in '\u0305\u0323' for ch in base)
            horizontal = shape(engine, base+tone)
            assert horizontal[:-1] == shape(engine, base)
            assert horizontal[-1][1:3] == (500, 0)
            for features in (None, {'vkrn': False}, {'ruby': True}):
                result = shape(engine, base+tone, 'ttb', features)
                assert result[:-1] == shape(engine, base, 'ttb', features)
                assert result[-1][1:3] == (0, 0)
                bounds = boxes(font, result)
                t = bounds[-1]
                assert t[0] >= max(b[2] for b in bounds[:-1])+20, (base, cp, bounds)
                assert -count*1000 <= t[1] < t[3] <= 0, (base, cp, bounds)
                assert abs((t[1]+t[3])/2 + count*500) < 180
                tone_cases += 1
        # A space or preceding tone ends the earlier syllable's context.
        single = shape(engine, 'チ'+tone, 'ttb')[-1]
        for prefix in ('チア𚿵', 'チア '):
            assert shape(engine, prefix+'チ'+tone, 'ttb')[-1] == single
        assert shape(engine, 'チ '+tone, 'ttb')[-1][1:3] == (0, -1000)

    joins = []
    for size in (32, 48, 128):
        count = components(mask(path, 0x1B11F, size))
        assert count == 2, (size, count)
        joins.append({'size_px': size, 'components': count})
    return {'source_forms': 15, 'mark_shaping_cases': mark_cases,
            'vertical_tone_cases': tone_cases, 'canonical_mark_orders_match': True,
            'isolated_tones_keep_vertical_cell': True,
            'wu_connectivity': joins}
