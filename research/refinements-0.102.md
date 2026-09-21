# GenZui Serif 0.102

This Regular development build adds 15 encoded characters and redraws archaic
hiragana WU. It contains 17,052 encoded characters, with 328 entries in the
historical-kana and support-mark inventory. The 20 GenZui constructions remain
provisional.

## Minnan kana

[FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana), by
Fredrick R. Brennan, supplies the 13 tone letters in Kana Extended-B and the
combining overline U+0305 and dot below U+0323. The source is pinned to commit
`5c367e9ee5aefd54b5c9c9e996705f0561fe3d15`. Its OFL copyright, licence and README
accompany the font.

The donor's 1000-unit em and outline proportions are retained. Cubic outlines
are converted to TrueType curves with a 0.3-unit approximation tolerance.
Tone letters keep their 500-unit horizontal advance. GenZui supplies new
attachment and vertical layout rules while retaining Noto's kana advances.

The overline sits above the kana. Small kana receive a narrower bar with the
same thickness. The dot sits below the base. Both marks have zero advances;
their canonical ordering does not alter the result.

Vertical tone forms have zero advance and sit beside the preceding group of
one to four kana. Isolated tone letters retain a full vertical cell. A previous
tone, space or punctuation ends the context. These rules assume default
fullwidth kana advances and zero letter spacing. Separate ruby annotations at
syllable boundaries. Longer groups and custom spacing require application-level
positioning.

References:

- [Unicode 18, Hiragana and Katakana](https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-18/)
- [L2/20-209R, Taiwanese kana proposal](https://www.unicode.org/L2/L2020/20209r-taiwan-kana.pdf)
- FRB's pinned `features.fea`, used as a layout reference

## Archaic hiragana WU

U+1B11F retains Noto's KE left stroke and crossbar and HO's upper bar. A new
stem ends in a short left return. The old long KE descent is removed. Stroke
width and the bar connections follow the surrounding Mincho kana.

Character structure was checked against
[L2/19-381](https://www.unicode.org/L2/L2019/19381-missing-kana.pdf) and
[L2/20-152](https://www.unicode.org/L2/L2020/20152-archaic-wu-origin.pdf).
Jigmo's WU provides a separate typeface comparison. These are references for
the new drawing; the outline is built from Noto components and original curves.

`minnan.html` shows the tones, marked syllables, horizontal ruby and the WU
comparison. The earlier ten-form comparison remains at `refinements.html`.

## Validation

`scripts/check_minnan.py` checks source bounds, metrics, mark clearance,
canonical order, small overlines, vertical groups, context boundaries and WU
connectivity. `scripts/check_serif.py` also verifies the complete Noto JP base,
all 290 imported historical outlines, the earlier refinements and matching
TTF/WOFF2 output. Browser and installation reports identify the checked font
bytes separately.
