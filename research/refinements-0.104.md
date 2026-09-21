# GenZui Serif 0.104

Eight encoded outlines change from 0.103. TOKI and the curved WU alternate
are retained. The font still contains 17,052 encoded characters and 21 GenZui
constructions, plus WU’s unencoded `ss01` alternate.

| Form | Revision |
| --- | --- |
| TOMO U+2A708 | TO and MO are reduced together to 92%, around the same centre. The taller MO proportion from 0.103 is retained. |
| KOTO U+1B123 | The lower TO bowl is 16% shallower, with its baseline retained. The upper connecting curve is lighter and extends into the space above the bowl. |
| Katakana NARI U+2CEFF | The lower entry is quieter. The inner edge gives more weight to the descending stroke and return; the low wave and overall horizontal span are retained. |
| Hiragana NARI U+2CF02 | The simpler diagonal-and-wave structure returns. The modern N-like entry is removed; the diagonal and low wave regain weight. The bottom remains at −32 units. |
| SHITE U+2CF00 | The side stroke has a rounded end and a short curved neck into the descent. The contours overlap, preserving the join at reading sizes. |
| WU U+1B11F | The hooked stem extends farther down and becomes narrower. Its head remains inside the top bar. The curved alternate is unchanged. |
| Alternate NE U+1B127 | The middle bar extends about 59 units farther left. The stem and right terminal stay in place. |
| Alternate WI U+1B128 | The lower left descent moves inward gradually, reaching 45 units at its foot. The upper stem and head remain unchanged. |

At y=250, katakana NARI’s descending stroke measures 72 units, up from 61
in 0.103. Its outer bounds are unchanged. WU’s hooked stem measures 64 units
at the same height, and its return reaches −58 units.

The NARI revisions use the earlier Jigmo and GenSeki specimens as structural
references. Both outlines are drawn in GenZui; no new donor outlines are
imported. The [previous research](refinements-0.103.md) records the Unicode
charts and printed specimens. KOTO retains its connected construction, with
more room for the upper turn.

The gallery compares the new outlines with a preserved 0.103 subset. Its WU
selector changes both comparison columns, so the hooked and curved forms can
be reviewed separately. The overlay follows the selected variant.

Validation checks the eight changed outlines against the baseline, unchanged
TOKI and curved WU, NARI stroke weight, and the extended WU stem. KOTO, SHITE
and both NARI forms are checked at 24, 32, 40, 48, 64 and 128 px. Full font
checks retain the JP and Hentaigana source outlines, mark attachment, vertical
layout and matching TTF/WOFF2 shaping. These remain provisional designs.
