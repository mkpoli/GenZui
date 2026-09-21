# Transcription additions in 0.113

Eleven characters bring the font to 17,064 encoded characters. All 18,319 glyphs
from 0.112 retain their outlines, advances and vertical metrics. Existing GSUB,
GPOS, BASE and ideographic variation sequences are preserved.

| Characters | Construction |
| --- | --- |
| 卄 U+5344 | Noto Serif CJK JP Regular 2.003, converted from CFF to TrueType curves; original advance and vertical origin retained |
| 𝍲𝍳𝍴𝍵𝍶 U+1D372–U+1D376 | Successive strokes of Noto Serif JP 正, at their original positions; the fifth mark retains the complete native glyph |
| ⿼ U+2FFC | Horizontal reflection of Noto’s ⿷ U+2FF7 |
| ⿽ U+2FFD | Horizontal reflection of Noto’s ⿺ U+2FFA |
| ⿾ U+2FFE | Noto’s dashed frame enclosing its horizontal double-headed arrow |
| ⿿ U+2FFF | A drawn clockwise half-turn arrow inside Noto’s dashed frame |
| ㇯ U+31EF | A minus sign inside Noto’s dashed frame |

The tally marks preserve the original stroke contours and overlaps. This keeps
the completed tally identical to 正 at reading sizes. The description symbols
use the same 30-unit frame strokes as the existing Noto symbols. All eleven
characters occupy one fullwidth cell in horizontal and vertical text.

The complete set of **17 ideographic-description characters** is now covered:
U+2FF0–U+2FFF and U+31EF. These display as visible operators; the font does not
compose a new character from an ideographic description sequence.

The specimen includes **Han numerals**, **Ideographic tally marks** and
**Ideographic description characters**. Each collection includes the related
characters from the Noto base. The numeral collection contains 80 supported
characters with Unicode Han script and a numeric type, including Suzhou numerals.
All three samples support horizontal and vertical writing. Each entry identifies
its outline source.

## Sources

The full Noto Serif CJK JP font supplies 卄, which is absent from the pinned
Noto Serif JP webfont source. It is pinned at commit
`f8d157532fbfaeda587e826d4cd5b21a49186f7c` in `sources/manifest.json`.
Its OFL and Adobe copyright accompany the derived font.

- [Noto Serif CJK sources](https://github.com/notofonts/noto-cjk/tree/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Serif)
- [Unicode tally-mark proposal, L2/16-046](https://www.unicode.org/L2/L2016/16046-ideo-tally-marks.pdf)
- [Counting Rod Numerals chart](https://www.unicode.org/charts/PDF/U1D360.pdf)
- [Ideographic Description Characters chart](https://www.unicode.org/charts/PDF/U2FF0.pdf)
- [CJK Strokes chart, including U+31EF](https://www.unicode.org/charts/PDF/U31C0.pdf)

Unicode charts provide shape references. Their font outlines are not used.
All added outlines derive from OFL Noto sources or GenZui drawing.

## Validation

[Font checks](refinement-checks-0.113.json) verify all previous outlines, metrics,
layout rules and variation sequences, the eleven additions in both writing
directions, progressive tally strokes and TTF/WOFF2 shaping parity.
[Browser font checks](browser-checks-0.113.json) cover all 340 inventory targets
in Chrome, Vivaldi and Firefox. [Specimen interaction checks](site-browser-checks-0.113.json)
exercise the three collection permalinks, source filtering, pagination, samples and
writing-direction controls in those three browsers. Reports identify the exact
font bytes tested.
