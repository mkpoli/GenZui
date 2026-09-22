"""Audit encoded kana coverage against the pinned Unicode 18 properties."""
import hashlib
import json

from fontTools.ttLib import TTFont
from repertoire import CJK_KANA, MINNAN_MARKS, properties
from sources import ROOT, verify
from honkoku import TALLIES

KANA_BLOCKS = ('Hiragana', 'Katakana', 'Katakana Phonetic Extensions',
               'Kana Extended-B', 'Kana Supplement', 'Kana Extended-A',
               'Small Kana Extension')


def check_coverage(path, report_path=None):
    """Require every assigned kana-script character and record additional scope."""
    manifest = verify()
    assigned = set(properties('DerivedAge.txt'))
    scripts = properties('Scripts.txt')
    extensions = properties('ScriptExtensions.txt')
    blocks = properties('Blocks.txt')
    names = {}
    for line in (ROOT/'data/unicode/UnicodeData.txt').read_text().splitlines():
        fields = line.split(';')
        names[int(fields[0], 16)] = fields[1]
    script_points = {cp for cp, script in scripts.items() if script in ('Hiragana', 'Katakana')}
    all_points = script_points | {cp for cp, value in extensions.items()
                                  if {'Hira', 'Kana'} & set(value.split())}
    scopes = {block: {cp for cp, value in blocks.items() if value == block} & assigned
              for block in KANA_BLOCKS}
    scopes.update({
        'Script Hiragana or Katakana': script_points,
        'Script plus Script_Extensions': all_points,
        'CJK-encoded kana ligatures': set(CJK_KANA),
        'Minnan combining marks': set(MINNAN_MARKS),
        'CJK numeral twenty (U+5344)': {0x5344},
        'Ideographic tally marks': set(TALLIES),
        'Ideographic description characters': set(range(0x2FF0, 0x3000)) | {0x31EF},
    })
    with TTFont(path) as font:
        covered = set(font.getBestCmap())
        version = font['name'].getDebugName(5).removeprefix('Version ')
    coverage = {label: {'total': len(points), 'covered': len(points & covered),
                        'missing': [{'cp': f'U+{cp:04X}', 'char': chr(cp),
                                     'name': names.get(cp, CJK_KANA.get(cp, ''))}
                                    for cp in sorted(points-covered)]}
                for label, points in scopes.items()}
    report = {
        'font_version': version, 'unicode_version': manifest['unicode_version'],
        'font_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'scope': 'Encoded character coverage; does not establish every historical glyph variant or combining sequence.',
        'sources': [f for f in manifest['files'] if f['path'].startswith('data/unicode/')],
        'coverage': coverage,
    }
    missing = {label: result['missing'] for label, result in coverage.items() if result['missing']}
    assert not missing, missing
    assert len(all_points) == 763, 'Review the pinned Unicode coverage scope if it changes.'
    report_path = report_path or ROOT/'research'/f'kana-coverage-{version}.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    from serif import OUT, STEM
    print(json.dumps(check_coverage(OUT/(STEM+'.ttf')), ensure_ascii=False, indent=2))
