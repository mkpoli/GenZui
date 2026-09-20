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

Neither operation establishes finished sans designs. Retained loops, disconnected
strokes and enclosed spaces need comparison with the upstream forms, followed by
manual edits. The small proof set is the basis for choosing the stroke treatment
before developing the rest of the repertoire.

The skeleton calculation uses scikit-image's CPU implementation on sixteen
1200-by-1250 masks, processed sequentially. It has no GPU implementation in this
build. The scripts perform no model inference.

## New outlines

The seven Unicode 18 additions require separately constructed serif and sans
outlines. Native Noto components provide stroke shapes, proportions and terminals.
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
