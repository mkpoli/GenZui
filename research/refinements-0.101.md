# Outline revisions in 0.101

Ten encoded outlines changed. The other 17,027 encoded outlines, including the
complete Noto Serif JP base and all 290 imported historical forms, are unchanged.
The font retains its family names and Regular weight.

| Character | Revision |
| --- | --- |
| 𪜈 U+2A708 TOMO | Native TO stem and MO upper bar, with a newly drawn connecting bar and rounded MO return. |
| 𛄧 U+1B127 alternate NE | Native WI crossbar with a redrawn kana-style upper turn and short curved return. |
| 𛄨 U+1B128 alternate WI | Native WI bars and right stem, with a full-width NA-derived left descent; bars moved closer without scaling. |
| 𛄣 U+1B123 KOTO | Redrawn upper curve with a continuous join into the native TO bowl. |
| 𛄤 U+1B124 TOKI | Native TO and KI stems at their original width; individually drawn crossbars join the left stem. |
| 𛄥 U+1B125 TOTE | The same TO stem, native TE top bar and descending stroke, with a newly drawn connecting bar. |
| 𛄦 U+1B126 YORI | Redrawn YO bars, an unscaled RI short stroke and a full-weight curved RI descent. |
| 𬼂 U+2CF02 hiragana NARI | Jigmo's normalized outline lowered 122 units, matching the bottom of Noto's ん. |
| 𬼀 U+2CF00 SHITE | Joined side stroke and a tapered, full-weight descending sweep. |
| 𬻿 U+2CEFF katakana NARI | Native SHI upper stroke with a newly drawn lower curve and rising exit. |

`scripts/serif_forms.py` contains the editable construction paths. It translates
native components without narrowing them. The new katakana forms retain Mincho
kana stroke treatment and remain provisional.

## References

[GenSeki Hentaigana Gothic 1.201](https://github.com/MihailJP/GenSekiHentaiganaGothic/releases/tag/v1.201)
was compared at the same em size. Its source table attributes the ligatures to
Sukima Gothic and the alternate NE/WI forms to GenSeki components. It supplies
useful comparisons for component spacing, the NARI return and SHITE's joined
stroke. The cached Sukima web subset does not include these ligatures; no claim
about its complete current binary is based on that subset.

[字躰帳変体仮名's published specimen](https://hentaigana.booth.pm/items/4889029)
provides a Mincho comparison for the historical kana. Its downloadable binary
requires sign-in and was not inspected. Neither its images nor its outlines are
embedded in GenZui.

Historical structures were checked against the Unicode proposals for
[KOTO, TOKI and TOTE](https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf),
[YORI](https://www.unicode.org/L2/L2024/24279-proposal-to-encode-kana-ligature.pdf)
and [alternate NE/WI](https://www.unicode.org/L2/L2025/25151-katakana-ne-wi.pdf).
The proposal specimens inform structure; their font data is not imported.
Kureedo's documented kana work also informed the method: preserve native stroke
weight, assess component spacing separately, and check the result in text.

## Verification

The connectivity check rasterizes each changed glyph at 48 and 128 px. KOTO,
TOKI and SHITE remain connected; TOTE's top bar, YORI's three components and
katakana NARI's upper stroke remain intentionally separate. At y=400, YORI's
RI strokes measure 61 and 69 units, compared with native RI's 61 and 65.
Hiragana NARI's bottom is −32 units, matching native ん.

The full font checks cover all 313 historical targets, mark attachment, vertical
forms, unchanged JP layout and equivalent TTF/WOFF2 output. The comparison page
adds reading sizes and vertical text; these mechanical checks do not establish
final typographic quality.
