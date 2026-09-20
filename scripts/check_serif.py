"""Check repertoire, retained outlines and horizontal/vertical shaping."""
import io
import json
import base64
import re

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from serif import FAMILY, OUT, SMALL, instance
from repertoire import repertoire


def shape(data, text, direction='ltr'):
    face = hb.Face(data)
    font = hb.Font(face)
    font.scale = (1000, 1000)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    buffer.direction = direction
    buffer.language = 'ja'
    hb.shape(font, buffer)
    return [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def check():
    path = OUT/'HKSerifProof-Regular.ttf'
    data = path.read_bytes()
    font = TTFont(path)
    cmap = font.getBestCmap()
    chars = repertoire()
    original = instance('NotoSerifHentaigana', 400)
    serialized = io.BytesIO()
    original.save(serialized)
    original = TTFont(io.BytesIO(serialized.getvalue()))
    source_cmap = original.getBestCmap()
    retained = 0
    marks_tested = 0
    for item in chars:
        ch = item['character']
        cp = ord(ch)
        assert cp in cmap, item['codepoint']
        name = cmap[cp]
        g = font['glyf'][name]
        assert g.numberOfContours != 0, name
        if cp in source_cmap:
            old_name = source_cmap[cp]
            old = original['glyf'][old_name]
            assert g.getCoordinates(font['glyf']) == old.getCoordinates(original['glyf']), name
            assert font['hmtx'][name] == original['hmtx'][old_name], name
            retained += 1
        horizontal = shape(data, ch)
        vertical = shape(data, ch, 'ttb')
        assert len(horizontal) == len(vertical) == 1, name
        assert horizontal[0][:3] == (font.getGlyphID(name), 1000, 0), name
        assert vertical[0][1:3] == (0, -1000), name
        if cp in SMALL:
            assert vertical[0][0] == font.getGlyphID(name+'.vert'), name
            vg = font['glyf'][name+'.vert']
            assert vg.xMin == g.xMin+140 and vg.yMin == g.yMin+190, name
        for mark in ('\u3099', '\u309a'):
            for direction in ('ltr', 'ttb'):
                shaped = shape(data, ch+mark, direction)
                assert len(shaped) == 2 and all(v[0] for v in shaped), (name,direction)
                assert shaped[1][1:3] == (0,0), (name,direction)
                assert sum(v[1] for v in shaped) == (1000 if direction == 'ltr' else 0)
                assert sum(v[2] for v in shaped) == (-1000 if direction == 'ttb' else 0)
                # Compare real outline boxes at the returned glyph origins.
                positions, x, y = [], 0, 0
                for gid, ax, ay, dx, dy in shaped:
                    gg = font['glyf'][font.getGlyphName(gid)]
                    positions.append((x+dx+gg.xMin,y+dy+gg.yMin,x+dx+gg.xMax,y+dy+gg.yMax))
                    x += ax
                    y += ay
                base_box, mark_box = positions
                if direction == 'ltr':
                    assert mark_box[1] >= base_box[3]+18, (name, direction, positions)
                    assert 0 <= mark_box[0] < mark_box[2] <= 1000, (name, direction, positions)
                    assert mark_box[3] <= font['OS/2'].usWinAscent
                else:
                    assert mark_box[0] >= base_box[2]+18, (name, direction, positions)
                    assert mark_box[3] <= 0, (name, direction, positions)
                marks_tested += 1
    web = TTFont(OUT/'HKSerifProof-Regular.woff2')
    web.flavor = None
    stream = io.BytesIO()
    web.save(stream)
    assert web.getBestCmap() == cmap
    for direction in ('ltr','ttb'):
        text = ''.join(item['character']+'\u3099' for item in chars)
        assert shape(data,text,direction) == shape(stream.getvalue(),text,direction)
    assert font['name'].getDebugName(1) == FAMILY
    assert font['OS/2'].usWeightClass == 400
    page = (OUT/'serif-proof.html').read_text()
    assert '/home/' not in page and 'data:font/woff2;base64,' in page
    embedded = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', page)
    assert len(embedded) == 2
    assert base64.b64decode(embedded[0]) == (OUT/'HKSerifProof-Regular.woff2').read_bytes()
    assert base64.b64decode(embedded[1]) == (OUT/'JP-Regular.woff2').read_bytes()
    assert page.count('<tr>') == 20 and 'LETTER SMALL KO' in page
    assert retained == 290 and len(chars) == 309
    report = {'target_characters':len(chars),'unchanged_historical_outlines':retained,
              'new_unicode18':sum(item['age']=='18.0' for item in chars),
              'small_vertical_alternates':len(SMALL),'mark_shaping_cases':marks_tested,
              'woff2_matches_ttf':True,'status':'passed'}
    (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    check()
