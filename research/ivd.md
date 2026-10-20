# Ideographic variation sequences

GenZui Serif and GenZui Sans keep Noto's Adobe-Japan1 sequences: 14,682 of the
14,684 registered in the collection. The [Ideographic Variation
Database](https://www.unicode.org/ivd/) (IVD) 2025-07-14 registers 29,635
sequences in six collections. Other collections often register a shape that
Adobe-Japan1 already covers, under a different selector. GenZui maps those
sequences to the glyph of the Adobe-Japan1 sequence. No outlines are added.

| Collection | Registered | Mapped in GenZui |
| --- | ---: | ---: |
| Adobe-Japan1 | 14,684 | 14,682 (from Noto) |
| Moji_Joho | 11,384 | 4,585 |
| Hanyo-Denshi | 13,045 | 4,646 |
| KRName | 36 | 28 |
| CAAPH | 198 | 19 |
| MSARG | 154 | 6 |

Hanyo-Denshi and Moji_Joho share 9,866 sequences, so the 5,137 mapped
sequences count under both where they are shared. The table is
`data/ivd/aliases.tsv`; each row gives the sequence, its collections and
identifiers, and the Adobe-Japan1 sequence and CID whose glyph it selects.

## Method

1. [Jigmo](https://kamichikoichi.github.io/jigmo/) 2025-09-12 implements every
   IVD sequence with [GlyphWiki](https://glyphwiki.org/) glyphs. When GlyphWiki
   unifies two sequences' shapes, Jigmo maps both to one glyph. A non-Adobe
   sequence whose Jigmo outline is identical to an Adobe-Japan1 sequence's on the
   same base character becomes an alias of that sequence. 5,142 sequences have
   such an outline. Three of them match two Adobe-Japan1 sequences on the base,
   which does not say which is meant, so they are dropped: U+59DA 姚 E0102 and
   E0103, U+6E23 渣 E0103.
2. IPAmj Mincho 006.01 is the reference font of the Moji_Joho collection. An
   alias is dropped when IPAmj draws the Moji_Joho sequences of one target with
   different outlines, or draws two targets' sequences alike. This removed
   U+80AD 肭 E0101 and E0103.
3. The build copies each font's own Adobe-Japan1 mapping to the alias, so Serif
   and Sans, Regular and Bold, each select their own glyph.

Near-identical outlines are not treated as equal. Within Jigmo, pairs that differ
by under 2% of their ink still include deliberate distinctions, such as 者 with
and without its dot. Comparing Jigmo or IPAmj renderings with Noto directly
picked the correct Adobe-Japan1 glyph in only 71–79% of a 400-character
calibration sample. The differences between variants are often single dots or
split radicals, so cross-font image matching is not used.

## Verification

Sixty mapped Moji_Joho sequences were rendered beside IPAmj's glyph for the same
sequence and IPAmj's other variants of the base character. Thirty were drawn at
random and thirty from characters with four or more Moji_Joho variants. All
sixty selected the IPAmj shape.

The 999 aliases that change Serif Regular's glyph were also reviewed by eye,
each beside the plain and variant forms of GenZui, IPAmj and Jigmo. The first
402 of them, the three outside the Basic Multilingual Plane and every sequence
through U+6F64 潤 E0104, have no wrong mapping.

`check_serif.py`, `check_bold.py`,
`check_sans.py` and `check_sans_bold.py` require every face's variation
sequences to equal Noto's plus the aliases. They also
require each alias to shape, horizontally and vertically, to the glyph of its
Adobe-Japan1 sequence.

## Not covered

| Collection | Unmapped | On characters GenZui lacks |
| --- | ---: | ---: |
| Moji_Joho | 6,799 | 2,469 |
| Hanyo-Denshi | 8,399 | 3,618 |
| CAAPH | 179 | 29 |
| MSARG | 148 | 68 |
| KRName | 8 | 0 |

Jigmo does not draw these sequences with the outline of exactly one
Adobe-Japan1 sequence on the same base, apart from the two IPAmj vetoed above.
Supporting them needs other evidence or new glyphs.

## Regenerating the table

```sh
.venv/bin/python scripts/ivd.py derive
```

The command fetches and verifies the files pinned in `sources/ivd-manifest.json`
and rewrites `data/ivd/aliases.tsv`. Builds read only the committed table.

## Sources

- Unicode Consortium, [Ideographic Variation Database](https://www.unicode.org/ivd/),
  `IVD_Sequences.txt` version 2025-07-14 (CAAPH registration).
- Koichi Kamichi and GlyphWiki contributors,
  [Jigmo](https://kamichikoichi.github.io/jigmo/) 2025-09-12 (`Jigmo.ttf`,
  `Jigmo2.ttf`, `Jigmo3.ttf`), CC0 1.0. Its unifications are GlyphWiki's
  community decisions. For Hanyo-Denshi-only, CAAPH, MSARG and KRName sequences
  they are the only evidence used.
- [GlyphWiki](https://glyphwiki.org/), the community-edited glyph database behind
  Jigmo. Each sequence has a page named after it, for example
  [u8fbb-ue0102](https://glyphwiki.org/wiki/u8fbb-ue0102) for 辻 E0102.
- Information-technology Promotion Agency (IPA), IPAmj Mincho 006.01
  (`ipamjm00601.zip`, 2019-05-30), IPA Font License v1.0, distributed for the
  [Moji Joho Kiban](https://moji.or.jp/mojikiban/font/) through
  [窓の杜](https://forest.watch.impress.co.jp/library/software/ipamjfont/).
  It is used only to check aliases. GenZui contains none of its outlines. The
  check covers Moji_Joho sequences only.
- 文字情報技術促進協議会, [MJ文字情報検索システム](https://moji.or.jp/mojikibansearch/basic).
  Its record for each MJ glyph name, for example
  [MJ025760](https://moji.or.jp/mojikibansearch/info?MJ%E6%96%87%E5%AD%97%E5%9B%B3%E5%BD%A2%E5%90%8D=MJ025760),
  gives the Moji_Joho reference glyph and its IVS.
