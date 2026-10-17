"""Storage and shaping checks for both Okinawan repertoires."""
from okinawan import DATA, ENTRIES, PUA


def check_okinawan(font, engine, web_engine, shape, boxes):
    cmap = font.getBestCmap()
    assert len(PUA) == 26
    assert font['OS/2'].ulUnicodeRange2 & (1 << 28), 'BMP PUA coverage bit'
    assert len([e for e in ENTRIES if e['system'] == 'funatsu']) == 27
    assert len([e for e in ENTRIES if e['system'] == 'prefecture']) == 8
    assert not set(PUA) & set(range(0xFA80, 0xFA9B))
    assert 0x1B168 not in PUA
    assert not {0xF464, 0xF466} & set(cmap)
    cases = 0
    for entry in ENTRIES:
        text = ''.join(chr(int(c, 16)) for c in entry['output'])
        for direction in ('ltr', 'ttb'):
            expected = shape(engine, text, direction)
            assert expected and all(g[0] for g in expected), entry['id']
            assert expected == shape(web_engine, text, direction), entry['id']
            if entry['system'] == 'prefecture':
                assert sum(g[1] for g in expected) == (500 if direction == 'ltr' else 0)
                if direction == 'ltr':
                    box = boxes(font, expected)[0]
                    assert 0 <= box[0] < box[2] <= 500 and 350 < box[1] < box[3] <= 880, box
            else:
                assert sum(g[1] for g in expected) == (1000 if direction == 'ltr' else 0)
                assert sum(g[2] for g in expected) == (-1000 if direction == 'ttb' else 0)
                if int(entry['output'][0], 16) in PUA:
                    assert len(expected) == 1, (entry['id'], expected)
                    for script in ('Latn', 'Zzzz', 'Hira', 'Kana', 'Hani'):
                        assert shape(engine, text, direction, script=script) == expected, (entry['id'], script)
            for box in boxes(font, expected):
                if direction == 'ltr':
                    assert box[3] <= font['OS/2'].usWinAscent
                    assert box[1] >= -font['OS/2'].usWinDescent
            cases += 1
        # A following modern kana must retain its original composition.
        for direction in ('ltr', 'ttb'):
            assert shape(engine, text+'か\u3099', direction)[-1:] == shape(engine, 'が', direction)
    assert len({e['id'] for e in ENTRIES}) == len(ENTRIES)
    return {'mapping_version': DATA['version'], 'pua_characters': len(PUA),
            'funatsu_forms': 27, 'raised_katakana': 8, 'shaping_cases': cases,
            'preferred_sequences': True, 'woff2_matches_ttf': True, 'status': 'passed'}
