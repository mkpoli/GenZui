# Design work

GenZui Serif / 源萃明朝 is a unified serif font containing Noto Serif JP's full repertoire
and historical kana. GenSeki Hentaigana Gothic covers the original 309-character
sans inventory, including all seven Unicode 18 additions. Its released Regular and Bold fonts serve as
the sans option.

## Unified Regular proof

`scripts/serif.py` builds one static Regular font with 17,052 encoded characters.
All 17,923 glyphs from Noto Serif JP, their horizontal and vertical metrics and
their original layout rules remain intact. The 290 historical outlines from Noto
Serif Hentaigana remain unchanged. Noto Serif JP supplies the existing digraphs
U+309F and U+30FF and components for the constructed forms:

- Hiragana WU defaults to a native KE-derived curved descent. Stylistic set 1
  selects quieter crossbars and one broad outward arc flowing through a compact drawn return.
  Both stems begin inside the upper bar.
- Hiragana KOTO uses accepted candidate E: a lower upper curve shifted left,
  a longer rising right stroke and a shallower TO bowl.
- Katakana TOKI and TOTE share an unscaled TO stem; their connecting bars are
  drawn individually. KI moves left with a slight shear to reduce its lean;
  TE retains its native strokes.
- Katakana YORI uses newly drawn YO bars, the native short RI stroke and a
  redrawn, full-weight curved RI descent.
- TOMO, alternate NE and alternate WI use native Mincho kana components and
  newly drawn joins and returns.
- SHITE and katakana NARI have redrawn Mincho outlines.
- Ten small forms use weight-500 source outlines at 72% scale. Their vertical
  forms move 140 units right and 190 units up. Small archaic YE uses the existing
  Noto Serif Hentaigana archaic YE outline.

Hiragana NARI retains the Japanese JMJ reference’s long diagonal. Native ん
supplies its brush entry, weight variation and rounded foot. Its low wave uses
the rounded finish of え and ends at −32. The gallery includes printed NARI references from 1899 and 1902.
Forms under review compare against 0.110; accepted forms appear once.
[The 0.111 notes](refinements-0.111.md) describe the construction and sources.

The font-menu name is `GenZui Serif`, localized as `源萃明朝` in Japanese.
The family reading is げんずい. `build/serif/sources.json` records each addition.
The new joins, spacing and stroke treatment require visual
review before expanding to further weights.

The 311 historical forms absent from JP have explicit dakuten and handakuten
anchors. A contextual `ccmp` substitution selects Hentaigana's mark outlines only
after those historical bases. Vertical substitutions select separate marks and
anchors. Modern Japanese retains JP's composition, positioning and vertical
substitutions, including the vertical form of ゟ. The historical forms have
1000-unit vertical advances; their marks have zero advances. JP's line metrics
remain unchanged.

Only historical glyphs and their mark outlines are imported from Hentaigana.
Its Latin glyphs and unrelated substitutions are excluded. This avoids duplicate
Latin coverage and preserves the JP font's ordinary text behaviour.

## Minnan kana

FRB Taiwanese Kana supplies 13 tone letters and U+0305/U+0323. The outlines
retain the donor’s em and weight; cubic curves are converted to TrueType curves.
New anchors position the marks above and below full and small katakana. Small
overlines are narrower without changing their thickness.

In horizontal text tones advance 500 units. After one to four fullwidth kana in
vertical text, contextual forms have zero advance and sit beside the group.
Isolated tones keep their own 1000-unit vertical cell. Default fullwidth metrics
and zero letter spacing are required; longer groups and custom spacing need
application-level positioning. [The 0.102 notes](refinements-0.102.md) give the
references and specimen.

## Sans study

The proof contains sixteen hentaigana alongside Noto Sans JP Regular. Its reference
is Noto Serif Hentaigana at weight 400. Both experimental treatments derive from
that font's weight-200 outlines:

- A expands the outlines by 21 units. This reduces relative stroke contrast but
  retains calligraphic terminals and some heavy joins.
- B traces a pruned skeleton, smooths the resulting paths and draws a 64-unit
  stroke with flat terminals. This removes most contrast; intersections, short
  branches and terminal directions require individual inspection.

Neither operation establishes finished sans designs. B's uniform stroke treatment
is the preferred direction, but its connections need revision. Incidental cursive
connecting strokes may be omitted where the character remains identifiable.
Junctions need deliberate contour construction; tracing every skeleton branch
produces short spurs and crowded joins.

[Existing sans fonts](existing-fonts.md) provide direct comparisons. Noto Sans
Hentaigana has editable upstream sources. GenSeki Hentaigana Gothic supplies a
released, fully encoded repertoire, drawing on Shokaki and Sukima. Evaluate these
outlines before expanding the automatic B treatment to the remaining characters.
Shokaki's U+1B060 and U+1B08B are useful examples of deliberate stroke separation.

The skeleton calculation uses scikit-image's CPU implementation on sixteen
1200-by-1250 masks, processed sequentially. It has no GPU implementation in this
build. The scripts perform no model inference.

## New outlines

The seven Unicode 18 additions need serif outlines. GenSeki
Hentaigana Gothic 1.201 already supplies sans outlines for all seven under OFL;
their proportions and construction need comparison with Noto Sans JP. Native
Noto components provide stroke shapes, proportions and terminals for further work.
Unicode chart glyphs and the following proposals document character identity and
historical structure; their embedded font data is not an outline source.

- Gen Kojitani, [L2/24-150, three kana ligatures](https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf):
  hiragana KOTO, katakana TOKI and TOTE, with printed examples.
- [L2/24-279, katakana YORI](https://www.unicode.org/L2/L2024/24279-proposal-to-encode-kana-ligature.pdf).
- Eiso Chan, [L2/25-151, alternate NE and WI](https://www.unicode.org/L2/L2025/25151-katakana-ne-wi.pdf).
- [Unicode 18 Small Kana Extension](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B130.pdf):
  SMALL ARCHAIC YE, used for Marshallese transliteration.

Hiragana ARCHAIC WU and the historical small kana are included in the first
serif proof. Their stroke weight and vertical positions remain part of the
visual review.

## Font behaviour

Each encoded historical character has direct cmap coverage in the same font as
the Japanese text. The proof does not introduce
optional `hist` or `hlig` conversion of ordinary kana sequences.

The four new digraphs have compatibility decompositions to ordinary kana
sequences. NFKC can therefore erase that encoding distinction. ALTERNATE NE and
ALTERNATE WI have no decomposition to their ordinary counterparts.

`scripts/check_serif.py` checks dakuten and handakuten attachment, horizontal and
vertical advances, small-kana positioning, all target code points and preservation
of the original historical outlines. It also compares every JP glyph and metric,
variation sequences, line metrics and 70 Japanese layout cases against the pinned
JP source. Browser rendering and visual inspection complement the shaping checks.

## Remaining design work

Review the twenty-one provisional forms beside ordinary kana at reading sizes before
deriving further weights. The 0.101 comparison page covers the redrawn joins,
stroke proportions and baseline adjustment. The current inventory contains 328
historical characters and support marks, including the four CJK-encoded ligatures
and the Minnan additions.
