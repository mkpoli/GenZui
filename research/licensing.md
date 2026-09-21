# Font licences

GenZui Serif uses Noto and FRB Taiwanese Kana sources under SIL OFL 1.1. The combined font is distributed under SIL OFL 1.1.
The exact files and their SHA-256 hashes are pinned in `sources/manifest.json`.

| Source | Material used | Copyright notices retained |
| --- | --- | --- |
| Noto Serif JP | Full Regular base and components for new kana | Google (package OFL header); Adobe (font metadata) |
| Noto Serif Hentaigana | 290 historical forms, combining marks and small archaic YE components | The Noto Project Authors |
| FRB Taiwanese Kana | 13 Minnan tone letters and two combining marks | Fredrick R. Brennan |
| Jigmo2, 2025-09-12 | U+2CF02 in historical comparison fonts through 0.102 | Koichi Kamichi and GlyphWiki contributors (credited in NOTICE.txt) |

The build records the notices from the OFL files and the source fonts' copyright
metadata in `OFL.txt` and the derived font's name table. The proof page includes
the combined licence. The original package licences remain in
`sources/upstream/<family>/OFL.txt`. Jigmo's archive supplies `LICENSE.txt`
(CC0), `README.txt` and `THANKS.txt`; all three accompany the distribution.
FRB’s original licence and README accompany the distribution as `FRB-OFL.txt`
and `FRB-README.md`. Its pinned source is
[FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana).
The [official Jigmo site](https://kamichikoichi.github.io/jigmo/) identifies the
font licence as CC0 1.0. The MIT licence of its build tools is separate.

Jigmo's CC0 material can be incorporated into the OFL derivative. The original
outlines retain their CC0 status; the bundled dedication records those terms.
Source attribution in `NOTICE.txt` records their use in the comparison fonts.
The current GenZui NARI is a new drawing.

## Modification and distribution

[OFL 1.1](https://openfontlicense.org/open-font-license-official-text/) permits
merging, modification, embedding and redistribution. The derived font remains
under OFL 1.1 and must retain the copyright notices and licence. The font may be
bundled with commercial software and used in commercial publications. The font
itself cannot be sold by itself. Documents and artwork made with it do not have
to use OFL.

The pinned Noto and FRB OFL headers do not declare a Reserved Font Name. The derivative
uses its own family identifier, `GenZui Serif` / `源萃明朝`, to distinguish it from
the original Noto releases. Attribution to the original authors does not imply endorsement.

Project scripts use `LICENSE-scripts.txt` (MIT). Derived outlines and the
resulting font use OFL 1.1. Unicode data uses `sources/Unicode-LICENSE.txt`.

## Other possible sources

[字躰帳変体仮名](https://booth.pm/ja/items/4889029) is advertised by its publisher
as a Source Han Serif derivative under OFL 1.1. Its download requires a BOOTH
account; the archive and its embedded notices have not been inspected. No outlines
from it are included in this build. Before reuse, inspect the actual package's
licence, copyright notices, character mappings and provenance.

The [Source Han Serif licence](https://github.com/adobe-fonts/source-han-serif/blob/master/LICENSE.txt)
declares the Reserved Font Name “Source”. A derivative using that source must
respect that restriction unless the holder grants permission. An independently
named family can combine compatible OFL sources while retaining their notices.

## Coverage and release status

The proof contains the full pinned Noto Serif JP repertoire plus all 328 characters
in the historical inventory. It uses Japanese regional glyph forms and supplies
Regular only. Twenty-one provisional outlines need typographic review. All four CJK-encoded kana are now GenZui constructions. These coverage and design limits are independent
of the licence permissions.
