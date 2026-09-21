# GenZui Serif 0.103

Seven encoded outlines change from 0.102. The remaining 17,045 encoded outlines
are unchanged. The repertoire stays at 17,052 characters. Hiragana NARI is now
a GenZui drawing, bringing the construction inventory to 21 code points:
eleven drawn forms and ten small optical adaptations. WU also has one
unencoded alternate, selected through OpenType `ss01`.

## WU variants

The hooked form remains the default. Its stem starts inside HO’s upper bar,
removing the head that projected above it in 0.102. The curved alternate keeps
the KE-derived descent used in 0.101, with the same correction at the upper bar.
Both right-hand contours reach 729 units, the top of the native HO bar.

Stylistic set 1 is named **Curved WU**. It substitutes only U+1B11F; it adds no
private-use encoding or variation selector. Both forms have 1000-unit advances
and support dakuten and handakuten in horizontal and vertical text. The gallery
selector changes the live text and outline preview together.

```css
font-family: "GenZui Serif", serif;
font-feature-settings: "ss01" 1;
```

The selector follows the [OpenType stylistic-set specification](https://learn.microsoft.com/en-us/typography/opentype/spec/features_pt#tag-ss01--ss20).

## Other outlines

| Character | Construction in 0.103 |
| --- | --- |
| TOKI U+1B124 | KI moves left by about 60 units at the crossbars. A small shear reduces its lean while preserving width at each height. The bars retain their rightward span. |
| TOMO U+2A708 | MO’s upper bar rises 62 units and its return drops 43 units. The longer body keeps the stroke weight of the previous construction. |
| KOTO U+1B123 | The upper curve has a fuller entry, compared against Noto KO. Native TO’s bowl is retained. |
| Katakana NARI U+2CEFF | The lower entry is fuller and its shoulder more rounded. The separate native SHI stroke is unchanged. |
| Hiragana NARI U+2CF02 | A new outline follows the Japanese reference’s low, open wave. Its head and descent use Noto N as a stroke reference; its exit is fuller. The baseline remains −32, aligned with Noto N. |
| SHITE U+2CF00 | A native NO-derived descent meets a newly drawn SHI-like side stroke. The side entry has more substance; the shared join remains continuous. |

## Shape references

The [Unicode Kana Extended-A chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B100.pdf)
provides the character structures for KOTO, TOKI and WU. The
[Extension C chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-2A700.pdf)
locates TOMO. The [Extension F chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-2CEB0.pdf)
shows Japanese references JMJ-056853 (katakana NARI), JMJ-056854 (SHITE), and
JMJ-056850 (hiragana NARI). NARI follows the Japanese low-wave form.

Printed references were inspected in the reproductions in
[L2/24-150](https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf):

- Figure 2: 手島継蔵『国語漢文自習要覧：附・仮名遣詳解』(1916), pp. 20–21.
- Figure 9: 落合直文ほか『普通日本文典』(1893), pp. 38–39.
- Figure 16: 松川半山『童蒙画引小学入門』(1875), p. 3.

These establish printed structures and proportions. The small reproduced
letterforms are insufficient to determine precise contour coordinates. Noto’s
こ・と・キ・モ・シ・ノ・ん・け・ほ supply the stroke and terminal comparisons.
No outlines were extracted from Unicode chart fonts or scanned books.
[Earlier research](refinements-0.101.md) records the GenSeki, Sukima and
Jitaicho comparisons. WU references also include
[L2/19-381](https://www.unicode.org/L2/L2019/19381-missing-kana.pdf) and
[L2/20-152](https://www.unicode.org/L2/L2020/20152-archaic-wu-origin.pdf).

## Gallery and validation

`gallery.html` shows GenZui constructions with a preserved 0.102 baseline.
Filters select drawn forms, the seven revisions, small optical adaptations,
or all 21 constructions. Reading size, vertical text, guides and an outline
overlay support comparison. Native reference glyphs are labelled separately.
The baseline subset has a recorded SHA-256 and source notice in
`research/baselines/`. Jigmo2 remains credited for NARI in the old comparison.

The font checks preserve every JP and Hentaigana source outline and exercise
both WU variants in five script contexts, two writing directions and with both
voicing marks. Raster checks cover 32, 48 and 128 px. Enabling `ss01` over the
full repertoire changes only WU. TTF and WOFF2 shaping must agree with the
feature on and off. The design remains provisional.
