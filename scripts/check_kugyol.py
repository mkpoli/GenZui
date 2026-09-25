"""Check GenZui Serif Kugyol and GenZui Sans Kugyol against their parents."""
import hashlib
import json

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from PIL import ImageFont

from gugyeol import PUA as GUGYEOL_PUA
from kugyol import FACES, OUT, SPACES

def outline(font, name):
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    return pen.glyph()


def name_records(font, nid):
    return {(r.platformID, r.platEncID, r.langID): r.toUnicode()
            for r in font['name'].names if r.nameID == nid}


def check_face(root, family, family_ja, style, parent_stem, kugyol_stem):
    parent = TTFont(root / f'{parent_stem}.ttf')
    sub_path = OUT / f'{kugyol_stem}.ttf'
    sub = TTFont(sub_path)

    parent_cmap = parent.getBestCmap()
    expected = set(GUGYEOL_PUA) | {cp for cp in SPACES if cp in parent_cmap}

    # cmap equals the parent's 구결 set plus the spaces the parent has.
    sub_cmap = sub.getBestCmap()
    assert set(sub_cmap) == expected, sorted(set(sub_cmap) ^ expected)
    assert len(sub_cmap) == len(GUGYEOL_PUA) + len(SPACES)

    # Every kept glyph's outline, advances and vertical metrics equal the parent's.
    for cp in sorted(expected):
        parent_name, sub_name = parent_cmap[cp], sub_cmap[cp]
        assert outline(parent, parent_name) == outline(sub, sub_name), hex(cp)
        assert parent['hmtx'][parent_name] == sub['hmtx'][sub_name], hex(cp)
        assert parent['vmtx'][parent_name] == sub['vmtx'][sub_name], hex(cp)
    # Face-wide vhea fields; the min/max side-bearing fields are recalculated
    # over the smaller glyph set, so only the constant fields are compared.
    for f in ('tableVersion', 'ascent', 'descent', 'lineGap', 'caretSlopeRise',
              'caretSlopeRun', 'caretOffset', 'metricDataFormat'):
        assert getattr(parent['vhea'], f) == getattr(sub['vhea'], f), f

    # Names: family / typographic family / PostScript name, mirroring the
    # parent's English + Japanese pattern, with no Korean (0x0412) record.
    assert name_records(sub, 1) == {(3, 1, 0x409): family, (3, 1, 0x411): family_ja}
    assert name_records(sub, 16) == {(3, 1, 0x409): family, (3, 1, 0x411): family_ja}
    assert name_records(sub, 2) == {(3, 1, 0x409): style, (3, 1, 0x411): style}
    assert name_records(sub, 17) == {(3, 1, 0x409): style, (3, 1, 0x411): style}
    assert name_records(sub, 6) == {(3, 1, 0x409): kugyol_stem}
    assert all(0x412 not in {lang for (_, _, lang) in name_records(sub, nid)}
               for nid in (0, 1, 2, 3, 4, 5, 6, 16, 17))
    assert sub['name'].getDebugName(5) == parent['name'].getDebugName(5)
    assert sub['name'].getDebugName(0) == parent['name'].getDebugName(0)
    assert sub['name'].getDebugName(13) == parent['name'].getDebugName(13)
    assert sub['name'].getDebugName(14) == parent['name'].getDebugName(14)
    assert sub['head'].fontRevision == parent['head'].fontRevision

    # fsType and the PUA range bit match the parent.
    assert sub['OS/2'].fsType == parent['OS/2'].fsType
    assert bool(sub['OS/2'].ulUnicodeRange2 & (1 << 28))
    assert bool(sub['OS/2'].ulUnicodeRange2 & (1 << 28)) == bool(parent['OS/2'].ulUnicodeRange2 & (1 << 28))

    # No layout tables reference only-dropped glyphs; none survive at all here.
    assert 'GSUB' not in sub and 'GPOS' not in sub

    # TTF and WOFF2 carry the same font.
    woff2 = TTFont(OUT / f'{kugyol_stem}.woff2')
    assert set(woff2.getBestCmap()) == expected

    # The file renders every kept code point with a non-empty bounding box.
    pil_font = ImageFont.truetype(str(sub_path), 64)
    for cp in sorted(expected):
        if cp in (0x20, 0x3000):
            continue
        bbox = pil_font.getbbox(chr(cp))
        assert bbox is not None and bbox[2] > bbox[0] and bbox[3] > bbox[1], hex(cp)

    return {
        'family': family, 'style': style,
        'encoded_characters': len(sub_cmap),
        'gugyeol_pua_characters': len(GUGYEOL_PUA),
        'ttf_sha256': hashlib.sha256((OUT / f'{kugyol_stem}.ttf').read_bytes()).hexdigest(),
        'woff2_sha256': hashlib.sha256((OUT / f'{kugyol_stem}.woff2').read_bytes()).hexdigest(),
    }


def check():
    reports = []
    for face in FACES:
        for style, (parent_stem, kugyol_stem) in face['styles'].items():
            reports.append(check_face(face['root'], face['family'], face['family_ja'],
                                       style, parent_stem, kugyol_stem))
    report = {'faces': reports, 'status': 'passed'}
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    check()
