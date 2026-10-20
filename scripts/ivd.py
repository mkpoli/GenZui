"""Ideographic Variation Database sequences that resolve to Adobe-Japan1 glyphs.

Noto's Japanese fonts implement the Adobe-Japan1 collection. Other collections
register their own sequences for many of the same shapes. Jigmo implements every
registered sequence with GlyphWiki glyphs and gives two sequences the same glyph
when GlyphWiki unifies their shapes. Such a sequence is an alias of the
Adobe-Japan1 sequence on the same base character, and selects the glyph the
font already uses for that sequence. IPAmj Mincho, the reference font of the
Moji_Joho collection, vetoes any alias whose Moji_Joho glyphs it draws apart.

`derive` writes the alias table from the pinned sources in
`sources/ivd-manifest.json`. Builds read only the committed table.
"""
import argparse
import collections
from fontTools.ttLib import TTFont

from sources import ROOT, verify

TABLE = ROOT/'data/ivd/aliases.tsv'
IVD = ROOT/'data/unicode/IVD_Sequences.txt'
JIGMO = [ROOT/'sources/upstream/Jigmo'/name for name in ('Jigmo.ttf', 'Jigmo2.ttf', 'Jigmo3.ttf')]
IPAMJ = ROOT/'sources/upstream/IPAmj/ipamjm.ttf'
AJ1 = 'Adobe-Japan1'
MJ = 'Moji_Joho'


def sequence(text):
    base, selector = text.split()
    return int(base, 16), int(selector, 16)


def label(key):
    return f'{key[0]:04X} {key[1]:X}'


def registry():
    """(base, selector) -> [(collection, identifier)] for every registered sequence."""
    result = collections.defaultdict(list)
    for line in IVD.read_text(encoding='utf-8').splitlines():
        if line.startswith('#') or ';' not in line:
            continue
        key, collection, identifier = (field.strip() for field in line.split(';'))
        result[sequence(key)].append((collection, identifier))
    return result


def outlines(path):
    """(base, selector) -> a key that is equal exactly when the outlines are."""
    font = TTFont(path)
    cmap, glyf = font.getBestCmap(), font['glyf']
    cache = {}

    def key(name):
        if name not in cache:
            cache[name] = glyf[name].compile(glyf)
        return cache[name]
    return {(cp, selector): key(name or cmap[cp])
            for table in font['cmap'].tables if table.format == 14
            for selector, pairs in table.uvsDict.items() for cp, name in pairs}


def derive():
    verify(fetch=True, manifest='ivd-manifest.json')
    ivd = registry()
    jigmo = {}
    for path in JIGMO:
        jigmo.update(outlines(path))
    assert set(ivd) <= set(jigmo), len(set(ivd) - set(jigmo))
    ipamj = outlines(IPAMJ)
    adobe = collections.defaultdict(lambda: collections.defaultdict(list))
    for key, entries in sorted(ivd.items()):
        if any(collection == AJ1 for collection, _ in entries):
            adobe[key[0]][jigmo[key]].append(key)
    # An outline shared by two Adobe-Japan1 sequences does not say which one is meant.
    aliases = {key: adobe[key[0]][jigmo[key]][0] for key, entries in ivd.items()
               if all(collection != AJ1 for collection, _ in entries)
               and len(adobe[key[0]].get(jigmo[key], ())) == 1}
    # IPAmj must draw every Moji_Joho sequence of one alias target alike, and
    # must not draw two targets' Moji_Joho sequences alike.
    targets, drawings = collections.defaultdict(set), collections.defaultdict(set)
    for key, target in aliases.items():
        if any(collection == MJ for collection, _ in ivd[key]):
            targets[target].add(ipamj[key])
            drawings[key[0], ipamj[key]].add(target)
    vetoed = {key for key, target in aliases.items()
              if len(targets[target]) > 1 or
              (key in ipamj and len(drawings[key[0], ipamj[key]]) > 1)}
    cids = {key: identifier for key, entries in ivd.items()
            for collection, identifier in entries if collection == AJ1}
    lines = [
        '# IVD sequences that select the glyph of an Adobe-Japan1 sequence on the same base.',
        '# Derived by scripts/ivd.py from IVD 2025-07-14, Jigmo 2025-09-12 (GlyphWiki',
        '# unification) and IPAmj Mincho 006.01 (Moji_Joho veto); see research/ivd.md.',
        '# sequence\tcollections\tadobe_japan1\tcid',
    ]
    for key in sorted(set(aliases) - vetoed):
        registered = ' '.join(f'{collection}:{identifier}' for collection, identifier in ivd[key])
        lines.append(f'{label(key)}\t{registered}\t{label(aliases[key])}\t{cids[aliases[key]]}')
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    TABLE.write_text('\n'.join(lines) + '\n')
    print(f'{len(aliases) - len(vetoed):,} aliases; IPAmj vetoed {len(vetoed)}: '
          + ', '.join(label(key) for key in sorted(vetoed)))


def aliases():
    """(base, selector) -> the Adobe-Japan1 (base, selector) it aliases."""
    return {sequence(fields[0]): sequence(fields[2])
            for line in TABLE.read_text().splitlines() if not line.startswith('#')
            for fields in [line.split('\t')]}


def expected(uvs):
    """The format 14 mapping a font with Adobe-Japan1 mapping `uvs` carries after `add_ivd`."""
    result = dict(uvs)
    for key, target in aliases().items():
        if target in uvs:
            assert result.setdefault(key, uvs[target]) == uvs[target], label(key)
    return result


def uvs(font):
    return {(cp, selector): name for table in font['cmap'].tables if table.format == 14
            for selector, pairs in table.uvsDict.items() for cp, name in pairs}


def add_ivd(font):
    """Map every alias whose Adobe-Japan1 sequence the font supports. Returns the count added."""
    table = next(t for t in font['cmap'].tables if t.format == 14)
    current = uvs(font)
    added = {key: name for key, name in expected(current).items() if key not in current}
    for (cp, selector), name in added.items():
        table.uvsDict.setdefault(selector, []).append((cp, name))
    for pairs in table.uvsDict.values():
        pairs.sort()
    return len(added)


def check_ivd(font, base, engine, shape):
    """The font keeps the base font's sequences and adds exactly the aliases it supports,
    and each alias shapes like its Adobe-Japan1 sequence."""
    original = uvs(base)
    assert uvs(font) == expected(original)
    supported = sorted((key, target) for key, target in aliases().items() if target in original)
    text = lambda keys: ''.join(chr(cp)+chr(selector) for cp, selector in keys)
    for direction in ('ltr', 'ttb'):
        assert ([g[:3] for g in shape(engine, text(k for k, _ in supported), direction)] ==
                [g[:3] for g in shape(engine, text(t for _, t in supported), direction)]), direction
    return {'aliases': len(supported), 'unsupported_targets': len(aliases()) - len(supported)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('command', choices=['derive'])
    parser.parse_args()
    derive()
