# GenZui Serif 0.105

Seven encoded outlines differ from 0.104. The remaining 17,045 encoded outlines,
including KOTO, TOKI, TOTE and YORI, are unchanged. WU’s curved `ss01` alternate
also remains unchanged. The repertoire is 17,052 encoded characters, with 328
historical kana and support marks.

| Form | Construction |
| --- | --- |
| TOMO U+2A708 | The stem meets the underside of the top bar through a shoulder based on native モ. Its 92% optical size is retained. |
| Katakana NARI U+2CEFF | The earlier low shoulder leads into a flatter lower sweep, with changing weight through the descent. The native シ upper stroke is retained. |
| Hiragana NARI U+2CF02 | The diagonal opens toward its foot; a rounder shoulder joins the low wave. The rising exit is lighter. The baseline remains at −32 units. |
| SHITE U+2CF00 | The native middle シ dot has a rounded body and a short curved connection to the ノ-derived descent. |
| WU U+1B11F | The hooked stem has a slight rightward bow. The crossbars have less curvature. Stem width at y=250 is 62 units; the return reaches −58. |
| Alternate NE U+1B127 | The top bar is fuller, and the middle bar sits 40 units lower. |
| Alternate WI U+1B128 | The lower left descent moves inward by up to 17 further units. |

Noto Serif JP’s モ and シ supply the T-junction and dot references. The NARI
structure is compared with the earlier Jigmo and GenSeki forms and the Japanese
references in the [Unicode Extension F chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-2CEB0.pdf):
JMJ-056853 and JMJ-056850. These NARI outlines are GenZui drawings.

## KOTO choices

The earlier top-bar studies use A (the current font), B (left entry 24 units
lower) and C (44 units lower). Four balance studies combine these entry angles
with a lower, left-shifted upper curve and a longer rising stroke on the right:

| Candidate | Entry | Upper curve left/down | Right stroke extension/up |
| --- | --- | --- | --- |
| D | B | 22 / 40 units | 72 / 24 units |
| E | C | 22 / 40 units | 72 / 24 units |
| F | B | 36 / 62 units | 100 / 32 units |
| G | C | 36 / 62 units | 100 / 32 units |

The displacements blend into the existing joins. The bottom bowl and its
baseline stay in place. Candidate fonts preserve horizontal and vertical
advances. Their vertical top bearings compensate for the lower top, preserving
the original vertical origin. The comparison therefore shows the shape change
at the same placement in both writing directions.

Each candidate can swap with any other A–G option. Its comparison menu selects
the second form; the outline, overlay and both reading directions follow that
selection. Earlier A/B/C studies sit
in an expandable section. The samples include と・𛄣・を and て・𛄣・あ.
All six alternatives are gallery proof fonts; A remains the installed default.

The references remain the [Unicode kana chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B100.pdf)
and historical specimens reproduced in
[L2/24-150](https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf).
The gallery provides horizontal and vertical context for every construction
and candidate. Swap changes the outline and reading font in the same position.

## Validation

The font checks preserve the JP base, Hentaigana forms, mark attachment,
vertical layout and the WU alternate. TOMO’s upper envelope is checked at 52
positions around the junction against its native モ bar. The maximum rounding
difference is one design unit. Seven connected forms are raster-checked at
24, 32, 40, 48, 64 and 128 px.

Gallery checks verify that each candidate changes only KOTO, preserves
advances and the vertical origin, and stays connected at reading sizes. B and C
retain the lower outline; D–G have the expected lower top and longer right
stroke. All characters in the horizontal and vertical samples have explicit
coverage in all eight embedded fonts. These checks establish geometry and rendering; visual review
of the provisional forms continues.
