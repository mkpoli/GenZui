"""Validate GenZui Sans Han: coverage, file split, outlines against their sources, shaping."""
import hashlib
import json

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from sans_han import FACES, OUT, SANS, SANS_STEM, SOURCES, VERSION, target

LIMIT = 65535


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_bounds(font, name):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    scale = 1000 / font['head'].unitsPerEm
    return None if pen.bounds is None else tuple(v * scale for v in pen.bounds)


def shaped(data, text, direction):
    font = hb.Font(hb.Face(data))
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.direction = direction
    hb.shape(font, buffer, {})
    return buffer.glyph_infos, buffer.glyph_positions


def check():
    record = json.loads((OUT/'sources.json').read_text())
    assert record['version'] == VERSION
    base = TTFont(SANS/(SANS_STEM+'.ttf'), lazy=True)
    assert digest(SANS/(SANS_STEM+'.ttf')) == record['base']['sha256'], 'Han was built against another GenZui Sans'
    base_cmap = set(base.getBestCmap())
    sources = {text: TTFont(path, lazy=True) for _, path, text in SOURCES}
    source_cmaps = {text: font.getBestCmap() for text, font in sources.items()}
    wanted = target()
    covered, report = set(base_cmap & wanted), {'family': 'GenZui Sans Han', 'version': VERSION, 'faces': {}}
    for face in FACES:
        path = OUT/(face['stem']+'.ttf')
        font = TTFont(path)
        cmap = font.getBestCmap()
        glyph_count = font['maxp'].numGlyphs
        assert glyph_count <= LIMIT, (face['stem'], glyph_count)
        assert all(cp >> 16 in face['planes'] for cp in cmap), face['stem']
        assert not set(cmap) & covered, 'A character appears in two files'
        assert not set(cmap) & base_cmap, 'A character duplicates GenZui Sans'
        assert set(cmap) <= wanted, 'A character outside the target repertoire'
        covered |= set(cmap)
        assert font['head'].unitsPerEm == 1000 and 'CFF ' not in font and 'glyf' in font

        # Each outline keeps its source's bounds within rounding and conversion error.
        source_of = {}
        for run in record['faces'][face['stem']]['runs']:
            for cp in range(int(run['first'][2:], 16), int(run['last'][2:], 16)+1):
                source_of[cp] = run['source']
        assert set(source_of) == set(cmap)
        glyphset, worst, advances = font.getGlyphSet(), 0.0, set()
        for cp, name in cmap.items():
            text = source_of[cp]
            expected = source_bounds(sources[text], source_cmaps[text][cp])
            pen = BoundsPen(glyphset)
            glyphset[name].draw(pen)
            if expected is None or pen.bounds is None:
                assert expected is None and pen.bounds is None, f'U+{cp:04X}'
                continue
            shift = (1000 - record['faces'][face['stem']]['recentred_source_widths'][f'U+{cp:04X}']) / 2 \
                if f'U+{cp:04X}' in record['faces'][face['stem']]['recentred_source_widths'] else 0
            expected = (expected[0]+shift, expected[1], expected[2]+shift, expected[3])
            error = max(abs(a-b) for a, b in zip(expected, pen.bounds))
            assert error <= 2, f'U+{cp:04X} drifts {error:.1f} units from {text}'
            worst = max(worst, error)
            advances.add(font['hmtx'][name][0])

        # Every file shapes its own characters without .notdef, in both directions.
        data = path.read_bytes()
        sample = ''.join(chr(cp) for cp in sorted(cmap)[::max(1, len(cmap)//400)])
        for direction in ('ltr', 'ttb'):
            infos, positions = shaped(data, sample, direction)
            assert all(info.codepoint for info in infos), (face['stem'], direction)
            if direction == 'ttb':
                assert all(p.y_advance == -1000 for p in positions)
        assert advances == {1000}, (face['stem'], sorted(advances))
        report['faces'][face['stem']] = {
            'family': face['family'], 'encoded_characters': len(cmap), 'glyphs': glyph_count,
            'by_source': record['faces'][face['stem']]['by_source'],
            'max_bounds_error_units': round(worst, 2), 'advance_widths': sorted(advances),
            'ttf_sha256': digest(path), 'woff2_sha256': digest(OUT/(face['stem']+'.woff2')),
            'ttf_bytes': path.stat().st_size, 'woff2_bytes': (OUT/(face['stem']+'.woff2')).stat().st_size,
        }
    missing = wanted - covered
    assert not missing, f'{len(missing)} target characters uncovered, e.g. U+{min(missing):04X}'
    report.update({'status': 'passed', 'target_characters': len(wanted),
                   'covered_by_genzui_sans': len(base_cmap & wanted),
                   'covered_by_han': len(covered) - len(base_cmap & wanted),
                   'base': record['base']})
    (OUT/'checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"Checked GenZui Sans Han {VERSION}: all {len(wanted):,} target characters covered; "
          + '; '.join(f"{k}: {v['encoded_characters']:,} characters, {v['glyphs']:,} glyphs, "
                      f"max drift {v['max_bounds_error_units']}" for k, v in report['faces'].items()))


if __name__ == '__main__':
    check()
