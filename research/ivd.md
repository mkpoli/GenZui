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
| Moji_Joho | 11,384 | 4,642 |
| Hanyo-Denshi | 13,045 | 4,696 |
| KRName | 36 | 28 |
| CAAPH | 198 | 21 |
| MSARG | 154 | 5 |

Hanyo-Denshi and Moji_Joho share 9,866 sequences, so the 5,199 mapped
sequences count under both where they are shared. The table is
`data/ivd/aliases.tsv`; each row gives the sequence, its collections and
identifiers, and the Adobe-Japan1 sequence and CID whose glyph it selects.

## Method

1. [GlyphWiki](https://glyphwiki.org/) draws every IVD sequence, each on a page
   named after it. Many of these drawings are GlyphWiki's copy of the
   registry's reference glyph, as U+550C 唌 E0101 is jmj-008320 for MJ008320.
   `scripts/ivd.py extract` reduces the GlyphWiki dump to one
   digest per sequence in `data/ivd/glyphwiki.tsv`. Two sequences with the same
   digest have identical strokes, also when one draws a component through a
   renamed copy of the other's.
2. A non-Adobe sequence with the same digest as exactly one Adobe-Japan1
   sequence on its base character becomes an alias of that sequence: 5,196
   sequences. U+6E23 渣 E0103 matches two, which does not say which is meant,
   so it is not mapped.
3. `data/ivd/review.tsv` adds three aliases whose GlyphWiki drawings differ only
   in whether a stroke starts with its own head or grows from the stroke it
   touches, or where a whole component sits: every stroke and every contact is
   the same. Each row states the difference. Sequences whose
   drawings differ in a stroke, a contact, a stroke's direction, or the length or
   spacing of strokes within a component are not mapped, such as U+550C 唌 E0101, where 廴 lacks
   the short stroke that Adobe-Japan1 E0100 draws at its corner.
4. IPAmj Mincho 006.01 is the reference font of the Moji_Joho collection. An
   alias is dropped when IPAmj draws the Moji_Joho sequences of one target with
   different outlines, or draws two targets' sequences alike. No current alias
   fails this check.
5. The build copies each font's own Adobe-Japan1 mapping to the alias, so Serif
   and Sans, Regular and Bold, each select their own glyph.

Near-identical drawings are not treated as equal by default. In
[Jigmo](https://kamichikoichi.github.io/jigmo/), a font of GlyphWiki glyphs,
pairs that differ by under 2% of their ink still include deliberate
distinctions, such as 者 with and without its dot. Comparing Jigmo or IPAmj
renderings with Noto directly picked the correct Adobe-Japan1 glyph in only
71–79% of a 400-character calibration sample. The differences between variants
are often single dots or split radicals, so cross-font image matching is not
used.

## Verification

Sixty mapped Moji_Joho sequences were rendered beside IPAmj's glyph for the same
sequence and IPAmj's other variants of the base character. Thirty were drawn at
random and thirty from characters with four or more Moji_Joho variants. All
sixty selected the IPAmj shape.

1,014 aliases change Serif Regular's glyph. Of the 412 among them through
U+6F64 潤 E0104 in label order, which puts the three outside the Basic
Multilingual Plane first, 402 were reviewed by eye beside the plain and variant
forms of GenZui, IPAmj and Jigmo, with no wrong mapping.

`check_serif.py`, `check_bold.py`,
`check_sans.py` and `check_sans_bold.py` require every face's variation
sequences to equal Noto's plus the aliases. They also
require each alias to shape, horizontally and vertically, to the glyph of its
Adobe-Japan1 sequence.

## Not covered

| Collection | Unmapped | On characters GenZui lacks |
| --- | ---: | ---: |
| Moji_Joho | 6,742 | 2,469 |
| Hanyo-Denshi | 8,349 | 3,618 |
| CAAPH | 177 | 29 |
| MSARG | 149 | 68 |
| KRName | 8 | 0 |

GlyphWiki draws none of these sequences like exactly one Adobe-Japan1 sequence
on the same base, and none is in the review list.
Supporting them needs other evidence or new glyphs.

## Regenerating the table

```sh
.venv/bin/python scripts/ivd.py extract dump.tar.gz
.venv/bin/python scripts/ivd.py derive
```

`extract` reads a GlyphWiki dump, downloaded from
`https://glyphwiki.org/dump.tar.gz`, and rewrites `data/ivd/glyphwiki.tsv`.
The dump is replaced daily, so the committed extract records the SHA-256 and
date of the one it came from. `derive` fetches and verifies the files pinned in
`sources/ivd-manifest.json` and rewrites `data/ivd/aliases.tsv` from the
extract and the review list. Builds read only the committed table.

## Sources

- Unicode Consortium, [Ideographic Variation Database](https://www.unicode.org/ivd/),
  `IVD_Sequences.txt` version 2025-07-14 (CAAPH registration).
- GlyphWiki Project and contributors, [GlyphWiki](https://glyphwiki.org/),
  `dump.tar.gz` of 2026-10-16 17:00 UTC (SHA-256
  6f9d8d2fe02982ffeff086bd7c9f3dee58d49db2b114f12e0d199efb8977b020), its
  `dump_newest_only.txt`. Its licence
  allows use, copying and redistribution with or without modification. Its
  drawings are the community's reading of each registry's reference glyph and
  are the only evidence used for Hanyo-Denshi-only, CAAPH, MSARG and KRName
  sequences. Each sequence has a page named after it, for example
  [u8fbb-ue0102](https://glyphwiki.org/wiki/u8fbb-ue0102) for 辻 E0102.
- Koichi Kamichi and GlyphWiki contributors,
  [Jigmo](https://kamichikoichi.github.io/jigmo/) 2025-09-12, CC0 1.0. Its
  outlines were the calibration sample for near-identical drawings and are
  shown in the visual review.
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
