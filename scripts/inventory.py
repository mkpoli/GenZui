"""Character inventory shared by the family pages: names, blocks, sources, groups."""
import unicodedata
from bisect import bisect_right

from repertoire import properties
from honkoku import TALLIES
from okinawan import PUA as OKINAWAN_PUA
from gugyeol import PUA as GUGYEOL_PUA, TWIN_CHARS as GUGYEOL_TWIN_CHARS
from sources import ROOT

KANA_GROUPS = {'hentaigana', 'historic-kana', 'small-kana', 'bmp-digraph',
               'cjk-kana-ligature', 'minnan-tone', 'phonetic-mark', 'compatibility-kana'}


def character_data(font, audit, source_kinds, descriptions=None):
    """source_kinds maps 'U+XXXX' to a short source key for the non-base characters."""
    descriptions = descriptions or {}
    cmap = font.getBestCmap()
    historic = {ord(c['character']): c for c in audit['characters']}
    ages = properties('DerivedAge.txt')
    numeric = properties('DerivedNumericType.txt')
    scripts = properties('Scripts.txt')
    blocks, starts = [], []
    for line in (ROOT/'data/unicode/Blocks.txt').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            extent, label = (s.strip() for s in line.split(';'))
            first, last = (int(s, 16) for s in extent.split('..'))
            blocks.append((first, last, label)); starts.append(first)
    names, ranges, first_range = {}, [], None
    for line in (ROOT/'data/unicode/UnicodeData.txt').read_text().splitlines():
        fields = line.split(';'); cp = int(fields[0], 16)
        if fields[1].endswith(', First>'):
            first_range = (cp, fields[2], fields[1])
        elif fields[1].endswith(', Last>'):
            ranges.append((first_range[0], cp, first_range[1], first_range[2]))
        elif cp in cmap:
            names[cp] = (fields[1], fields[2])
    for first, last, category, range_name in ranges:
        for cp in (c for c in cmap if first <= c <= last):
            if range_name.startswith('<CJK Ideograph'):
                name = f'CJK UNIFIED IDEOGRAPH-{cp:04X}'
            elif range_name.startswith('<Hangul Syllable'):
                name = unicodedata.name(chr(cp))  # Stable algorithmic names.
            else:
                assert category == 'Co', range_name
                name = f'PRIVATE USE-{cp:04X}'
            names[cp] = (name, category)
    entries = []
    for cp in sorted(cmap):
        assert cp in names, f'Missing Unicode name: U+{cp:04X}'
        name, category = names[cp]
        index = bisect_right(starts, cp)-1
        assert index >= 0 and cp <= blocks[index][1]
        h = historic.get(cp)
        key = f'U+{cp:04X}'
        source = source_kinds[key] if h or cp in OKINAWAN_PUA or cp in GUGYEOL_PUA else 'jp'
        if cp in OKINAWAN_PUA:
            name = 'OKINAWAN ' + OKINAWAN_PUA[cp]['label'].upper() + ' (PRIVATE USE)'
        elif cp in GUGYEOL_PUA:
            name = f'GUGYEOL TWIN {GUGYEOL_TWIN_CHARS[cp]} (PRIVATE USE)'
        group = ('okinawan' if cp in OKINAWAN_PUA else 'gugyeol' if cp in GUGYEOL_PUA else
                 'han-numeral' if cp in numeric and scripts.get(cp) == 'Han' else
                 'ideographic-description' if 0x2FF0 <= cp <= 0x2FFF or cp == 0x31EF else
                 'tally-mark' if cp in TALLIES else h['group'] if h else 'base')
        entries.append({'cp': cp, 'name': name, 'category': category,
                        'block': blocks[index][2],
                        'age': 'Private use' if cp in OKINAWAN_PUA or cp in GUGYEOL_PUA else ages[cp],
                        'source': source, 'group': group,
                        'label': h.get('label', name) if h else name,
                        'provisional': source == 'genzui',
                        'description': descriptions.get(key, '')})
    return entries
