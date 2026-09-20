# Design work

The active work is a unified serif font containing Noto Serif JP's full repertoire
and historical kana. GenSeki Hentaigana Gothic covers the complete sans target, including
all seven Unicode 18 additions. Its released Regular and Bold fonts serve as
the sans option.

## Unified Regular proof

`scripts/serif.py` builds one static Regular font with 17,033 encoded characters.
All 17,923 glyphs from Noto Serif JP, their horizontal and vertical metrics and
their original layout rules remain intact. The 290 historical outlines from Noto
Serif Hentaigana remain unchanged. Noto Serif JP supplies the existing digraphs
U+309F and U+30FF and components for the seventeen missing forms:

- Hiragana WU combines KE strokes with HO's upper bar.
- Hiragana KOTO uses TO's bowl with a newly drawn upper curve.
- Katakana TOKI and TOTE combine a TO stem with KI or TE.
- Katakana YORI combines YO with two upright stems.
- Alternate NE and WI use U+5B50 and U+4E95 fitted to the kana body. Their kanji
  terminals need further comparison with the kana style.
- Ten small forms use weight-500 source outlines at 72% scale. Their vertical
  forms move 140 units right and 190 units up. Small archaic YE uses the existing
  Noto Serif Hentaigana archaic YE outline.

The internal font-menu identifier is `HK Serif Proof`. It is not a proposed
family name. `build/serif/sources.json` records the construction of each addition.
The new joins, spacing, reduced stroke weight and NE/WI terminals require visual
review before expanding to further weights.

The 307 historical forms absent from JP have explicit dakuten and handakuten
anchors. A contextual `ccmp` substitution selects Hentaigana's mark outlines only
after those historical bases. Vertical substitutions select separate marks and
anchors. Modern Japanese retains JP's composition, positioning and vertical
substitutions, including the vertical form of ゟ. The historical forms have
1000-unit vertical advances; their marks have zero advances. JP's line metrics
remain unchanged.

Only historical glyphs and their mark outlines are imported from Hentaigana.
Its Latin glyphs and unrelated substitutions are excluded. This avoids duplicate
Latin coverage and preserves the JP font's ordinary text behaviour.

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

Review the seventeen provisional forms against historical specimens, especially
KOTO's upper curve, the TOKI/TOTE joins and NE/WI terminals. Check their weight
beside ordinary kana at reading sizes before deriving further weights. The
CJK-encoded kana ligatures U+2A708, U+2CEFF, U+2CF00 and U+2CF02 need a separate
source and design audit; they are outside the current 309-character inventory.
