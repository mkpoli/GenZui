# Design work

The serif family follows Noto Serif JP and Noto Serif Hentaigana. The sans family
follows Noto Sans JP, with a distinct sans outline for every hentaigana. Serif
fallback does not satisfy the sans coverage target.

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

The seven Unicode 18 additions need outlines matched to each family. GenSeki
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

Hiragana ARCHAIC WU and the historical small kana absent from the source fonts
also need outlines. Small kana must follow each JP family's small-letter scale,
stroke weight and vertical position.

## Font behaviour

Each encoded historical character needs direct cmap coverage. Ordinary kana
retain their default forms. Optional `hist`/character-variant substitutions can
select alternate NE and WI; optional `hlig` substitutions can select digraphs
from ordinary kana sequences. These features must not alter the stored text.

The four new digraphs have compatibility decompositions to ordinary kana
sequences. NFKC can therefore erase that encoding distinction. ALTERNATE NE and
ALTERNATE WI have no decomposition to their ordinary counterparts.

Production checks must cover dakuten and handakuten attachment, horizontal and
vertical advance, small-kana positioning, clipping, all target code points, and
preservation of the JP source's default forms. These checks are broader than the
current unmarked-form proof checks.
