# 源萃 GenZui

Public specimen and downloads: https://genzui.mkpo.li/. Related typeface: [Kureedo](https://kureedo.mkpo.li/).

GenZui (源萃, げんずい) combines established fonts with historical kana extensions.
The serif family is **GenZui Serif / 源萃明朝**. Noto Serif JP supplies the full
Japanese base; Noto Serif Hentaigana supplies 290 historical forms. FRB Taiwanese Kana supplies 13 Minnan tone letters and two
combining marks. Twenty-one provisional constructions complete the 328-character
historical and support-mark inventory, including all seven Unicode 18
kana additions. The font contains 17,052 encoded characters.

Version 0.111 is the first public release, available as a static Regular font. Historical katakana use
Mincho kana strokes. The twenty-one constructed forms need typographic
review before a stable release. Shared ideographs use
Japanese regional forms; Chinese and Korean coverage is limited to the JP base.
GenSeki Hentaigana Gothic serves as the existing sans companion. The
[font survey](research/existing-fonts.md) documents the alternatives and the
sans study. GenZui is developed separately from Kureedo.

## Build GenZui Serif

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/sources.py
.venv/bin/python scripts/repertoire.py
.venv/bin/python scripts/serif.py
.venv/bin/python scripts/check_serif.py
```

`build/serif/` contains `GenZuiSerif-Regular.ttf`, its WOFF2 counterpart, the
self-contained `serif-proof.html`, outline provenance, licences and validation
results. The specimen includes editable mixed text, vertical text, combining
marks, all hentaigana and a table of the constructed forms, NARI and Minnan additions.

Checks cover all 328 historical characters and support marks, preservation of the 290 original
historical outlines, all 17,923 JP glyphs and their metrics, JP variation
sequences, 70 Japanese layout comparisons, ten vertical small-kana forms,
1,244 historical mark-shaping cases, the redrawn NARI baseline, both WU variants, localized
family names and matching TTF/WOFF2 output. Minnan checks cover 195 vertical tone
cases and 88 combining-mark cases. The two existing JP digraphs retain
their original mark behaviour. These checks establish font behaviour; the
provisional outlines still require typographic review.

After Windows browser validation, `.venv/bin/python scripts/package_serif.py`
produces `dist/GenZuiSerif-Regular-0.105.zip`. It includes fonts, an offline
specimen, licences, provenance, validation reports and an optional per-user
Windows installer. Packaging requires passing Chrome, Vivaldi and Firefox
reports for the exact font bytes.

## Specimen site

After packaging the font, run `.venv/bin/python scripts/site.py` and open
`build/site/index.html`. The page embeds the font and works offline. It includes
an editable horizontal/vertical specimen, a searchable inventory of all 17,052
encoded characters, source details and provisional-outline labels. Filters
isolate the hentaigana, Unicode 18 additions, small kana, ligatures and Minnan letters and marks.

`gallery.html` isolates the 11 drawn forms and ten small optical adaptations.
Accepted forms appear once; forms under review have 0.110 comparisons, swapping,
overlays and Noto stroke references. Every specimen has horizontal and vertical
context. KOTO uses accepted candidate E. WU defaults to the curved form;
OpenType stylistic set 1 (`ss01`, “Hooked WU”) selects the hooked form.
Both WU forms retain U+1B11F; the selector compares the same form across versions.
TOMO appears between TOKI and TOTE, with native kana references for its nearby
stroke entries.
Run `scripts/check_gallery.py` after the site build to verify the embedded fonts.
[The 0.111 notes](research/refinements-0.111.md) document the outlines and sources.

`minnan.html` demonstrates tone placement, combining marks, ruby and both WU forms.
[The 0.102 notes](research/refinements-0.102.md) describe the Minnan layout limits.

`refinements.html` compares the ten revised forms with 0.100, with reading-size
and vertical-text controls. [Revision notes](research/refinements-0.101.md)
describe their construction and the references used.

`dist/GenZui-Specimen-0.111.zip` contains the specimen pages and the font downloads.
Keep the `downloads/` directory beside `index.html`. Edit the HTML, CSS and
JavaScript in `site/`, then rebuild; character data comes from the checked font
and pinned Unicode files. Windows Chrome, Vivaldi and Firefox interaction
results are recorded in `research/site-browser-checks.json`.

## Sources and coverage

| Source | Role | Historical targets covered |
| --- | --- | ---: |
| Noto Serif JP | Full Japanese base and construction components | 2 |
| Noto Serif Hentaigana | Hentaigana outlines and historical forms | 290 |
| FRB Taiwanese Kana | Minnan tone letters and two combining marks | 15 |
| GenZui constructions | Noto components and original drawing | 21 |

The repertoire in `research/repertoire.json` contains 286 hentaigana, 11 other
letters and digraphs in Kana Supplement and Kana Extended-A, ten small kana,
ゟ and ヿ, four CJK-encoded kana ligatures, 13 Minnan tone letters and two
combining marks. Those four are 𪜈 TOMO (U+2A708),
𬻿 katakana NARI (U+2CEFF), 𬼀 SHITE (U+2CF00), and 𬼂 hiragana NARI (U+2CF02).
Their identities are documented in
[L2/24-150](https://www.unicode.org/L2/L2024/24150-three-kana-ligatures.pdf).

CODH's [hentaigana page](https://codh.rois.ac.jp/char-shape/hentaigana/) presents
both NINJAL's font and Noto Serif Hentaigana. The hentaigana outline source here
is [Noto Serif Hentaigana](https://github.com/notofonts/hentaigana), under OFL 1.1.
The comparison fonts through 0.102 use [Jigmo2](https://kamichikoichi.github.io/jigmo/)
for hiragana NARI under CC0 1.0; the current outline is a GenZui drawing. No NINJAL outlines or scanned specimen images are embedded.

### Unicode 18 additions

| Code point | Character |
| --- | --- |
| U+1B123 | Hiragana digraph KOTO |
| U+1B124 | Katakana digraph TOKI |
| U+1B125 | Katakana digraph TOTE |
| U+1B126 | Katakana digraph YORI |
| U+1B127 | Katakana letter ALTERNATE NE |
| U+1B128 | Katakana letter ALTERNATE WI |
| U+1B168 | Katakana letter SMALL ARCHAIC YE |

These seven use GenZui constructions. Character names, ages, decompositions and
vertical orientation come from the pinned Unicode 18.0.0 data files.

References: [Kana Extended-A chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B100.pdf),
[Small Kana Extension chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B130.pdf).

## Reproducibility

`sources/manifest.json` pins fonts to Git commits and records every source file's
SHA-256. Jigmo files are extracted from its pinned release archive, with both
archive and member checksums verified. A cached source with an unexpected
checksum causes a build error.

The sixteen-character sans study is built with `scripts/proof.py` and checked
with `scripts/check.py`. Its construction methods are documented in
[research/design.md](research/design.md). Noto Sans JP supplies the sans context.

## Windows

Double-click the TTF and choose **Install**, or run the package's
`Install-GenZui.ps1` from PowerShell. The installed family appears as **GenZui
Serif** or **源萃明朝**, depending on the application's language. Reopen an
application if its font list does not update.

[Browser setup](browser/README.md) covers the existing GenSeki fallback for
Firefox, Chrome, Vivaldi and Windows Terminal. Installing GenZui makes the family
available but does not establish a universal fallback order. On a page you
control, use `font-family: "GenZui Serif", "源萃明朝", serif` to select it.

## Licence

The combined font uses SIL OFL 1.1. Noto and FRB Taiwanese Kana use OFL 1.1;
Jigmo2 uses CC0 1.0.
`OFL.txt` and font metadata retain the Google, Adobe and Noto Project copyright
notices, together with Fredrick R. Brennan’s FRB copyright. `NOTICE.txt` credits the outline sources. Jigmo's CC0 text, README and
contributor notices accompany the distribution. Its original CC0 dedication
remains in effect. [Licence details](research/licensing.md) document reuse.
Unicode data uses `sources/Unicode-LICENSE.txt`. Project scripts and the Windows
installer use the MIT licence in `LICENSE-scripts.txt`.
