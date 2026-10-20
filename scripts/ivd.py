"""Ideographic Variation Database sequences that resolve to Adobe-Japan1 glyphs.

Noto's Japanese fonts implement the Adobe-Japan1 collection. Other collections
register their own sequences for many of the same shapes. GlyphWiki draws every
registered sequence; when two sequences of one base character have the same
drawing there, the non-Adobe sequence is an alias of the Adobe-Japan1 one and
selects the glyph the font already uses for it. `data/ivd/review.tsv` adds the
aliases whose GlyphWiki drawings differ only in how a stroke joins another or
where a component sits. IPAmj Mincho, the reference font of the Moji_Joho
collection, vetoes any alias whose Moji_Joho glyphs it draws apart.

`extract` reduces a GlyphWiki dump to `data/ivd/glyphwiki.tsv`. `derive` writes
the alias table from that extract, the review list and the pinned sources in
`sources/ivd-manifest.json`. Builds read only the committed table.
"""
import argparse
import collections
import datetime
import hashlib
import tarfile
from fontTools.ttLib import TTFont

from sources import ROOT, verify

TABLE = ROOT/'data/ivd/aliases.tsv'
GLYPHWIKI = ROOT/'data/ivd/glyphwiki.tsv'
REVIEW = ROOT/'data/ivd/review.tsv'
IVD = ROOT/'data/unicode/IVD_Sequences.txt'
IPAMJ = ROOT/'sources/upstream/IPAmj/ipamjm.ttf'
AJ1 = 'Adobe-Japan1'
MJ = 'Moji_Joho'


def sequence(text):
    base, selector = text.split()
    return int(base, 16), int(selector, 16)


def label(key):
    return f'{key[0]:04X} {key[1]:X}'


def rows(path):
    return [line.split('\t') for line in path.read_text(encoding='utf-8').splitlines()
            if line and not line.startswith('#')]


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


def drawings(kage):
    """Glyph name -> a digest; equal digests mean GlyphWiki draws the same strokes.

    Components are replaced by their own digests, so renamed copies of one
    drawing compare equal; a glyph that is a single full-size reference is the
    glyph it references. Versioned references (`name@3`) stay as written, and
    the same strokes written in another order or with a component inlined get a
    different digest."""
    memo = {}

    def digest(name, stack=()):
        if name in memo:
            return memo[name]
        if name not in kage or name in stack:
            return 'ref:' + name
        lines = []
        for line in kage[name].split('$'):
            fields = line.split(':')
            if fields[0] == '99' and len(fields) >= 8:
                extra = fields[8:]
                while extra and extra[-1] == '0':
                    extra.pop()
                fields = fields[:7] + [digest(fields[7], stack + (name,))] + extra
            lines.append(':'.join(fields))
        if len(lines) == 1 and lines[0].startswith('99:0:0:0:0:200:200:') and lines[0].count(':') == 7:
            result = lines[0].removeprefix('99:0:0:0:0:200:200:')
        else:
            result = hashlib.sha256('$'.join(lines).encode()).hexdigest()[:16]
        memo[name] = result
        return result
    return digest


def extract(dump):
    """Write each registered sequence's GlyphWiki drawing digest from `dump.tar.gz`."""
    with open(dump, 'rb') as file:
        archive = hashlib.file_digest(file, 'sha256').hexdigest()
    kage = {}
    with tarfile.open(dump) as tar:
        member = tar.getmember('dump_newest_only.txt')
        for line in tar.extractfile(member).read().decode('utf-8').splitlines():
            fields = line.split('|')
            if len(fields) >= 3 and (name := fields[0].strip()) and name != 'name':
                kage[name] = fields[2].strip()
    digest = drawings(kage)
    lines = [
        '# GlyphWiki drawing of every IVD sequence: equal digests mean the same strokes.',
        f'# From dump.tar.gz (sha256 {archive}), dump_newest_only.txt of',
        f'# {datetime.datetime.fromtimestamp(member.mtime, datetime.UTC):%Y-%m-%d %H:%M} UTC;'
        ' https://glyphwiki.org/; written by scripts/ivd.py extract.',
        '# sequence\tdrawing',
    ]
    lines += [f'{label(key)}\t{digest(f"u{key[0]:x}-u{key[1]:x}")}' for key in sorted(registry())]
    GLYPHWIKI.write_text('\n'.join(lines) + '\n')


def derive():
    verify(fetch=True, manifest='ivd-manifest.json')
    ivd = registry()
    glyphwiki = {sequence(key): drawing for key, drawing in rows(GLYPHWIKI)}
    assert set(glyphwiki) == set(ivd), len(set(ivd) ^ set(glyphwiki))
    ipamj = outlines(IPAMJ)
    adobe = collections.defaultdict(lambda: collections.defaultdict(list))
    for key, entries in sorted(ivd.items()):
        if any(collection == AJ1 for collection, _ in entries):
            adobe[key[0]][glyphwiki[key]].append(key)
    # A drawing shared by two Adobe-Japan1 sequences does not say which one is meant.
    aliases = {key: adobe[key[0]][glyphwiki[key]][0] for key, entries in ivd.items()
               if all(collection != AJ1 for collection, _ in entries)
               and len(adobe[key[0]].get(glyphwiki[key], ())) == 1}
    for key, target, _ in rows(REVIEW):
        key, target = sequence(key), sequence(target)
        # A review row covers only a sequence GlyphWiki draws unlike every Adobe-Japan1 one.
        assert glyphwiki[key] not in adobe[key[0]] and key[0] == target[0], label(key)
        assert any(c == AJ1 for c, _ in ivd[target]) and all(c != AJ1 for c, _ in ivd[key]), label(key)
        aliases[key] = target
    # IPAmj must draw every Moji_Joho sequence of one alias target alike, and
    # must not draw two targets' Moji_Joho sequences alike.
    targets, shapes = collections.defaultdict(set), collections.defaultdict(set)
    for key, target in aliases.items():
        if any(collection == MJ for collection, _ in ivd[key]):
            targets[target].add(ipamj[key])
            shapes[key[0], ipamj[key]].add(target)
    vetoed = {key for key, target in aliases.items()
              if len(targets[target]) > 1 or
              (key in ipamj and len(shapes[key[0], ipamj[key]]) > 1)}
    cids = {key: identifier for key, entries in ivd.items()
            for collection, identifier in entries if collection == AJ1}
    lines = [
        '# IVD sequences that select the glyph of an Adobe-Japan1 sequence on the same base.',
        '# Derived by scripts/ivd.py from IVD 2025-07-14, GlyphWiki (data/ivd/glyphwiki.tsv),',
        '# data/ivd/review.tsv and IPAmj Mincho 006.01 (Moji_Joho veto); see research/ivd.md.',
        '# sequence\tcollections\tadobe_japan1\tcid',
    ]
    for key in sorted(set(aliases) - vetoed):
        registered = ' '.join(f'{collection}:{identifier}' for collection, identifier in ivd[key])
        lines.append(f'{label(key)}\t{registered}\t{label(aliases[key])}\t{cids[aliases[key]]}')
    TABLE.write_text('\n'.join(lines) + '\n')
    print(f'{len(aliases) - len(vetoed):,} aliases; IPAmj vetoed {len(vetoed)}',
          *(label(key) for key in sorted(vetoed)))


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
    parser.add_argument('command', choices=['extract', 'derive'])
    parser.add_argument('dump', nargs='?', help='GlyphWiki dump.tar.gz, for extract')
    args = parser.parse_args()
    if args.command == 'extract' and not args.dump:
        parser.error('extract needs the path of dump.tar.gz')
    extract(args.dump) if args.command == 'extract' else derive()
