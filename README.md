# 源萃明朝 GenZui Serif

GenZui (源萃, げんずい) is a Japanese Mincho font derived from **Noto Serif JP**,
**Noto Serif Hentaigana**, **Noto Serif CJK JP** and **FRB Taiwanese Kana**, with drawn historical kana
and Unicode 18.0 additions. Version **0.114** contains **17,090 encoded characters**
in one Regular weight.

Version 0.114 adds an [Okinawan composer](https://genzui.mkpo.li/serif#okinawan) to the
home page, with Funatsu’s 27 forms and the prefecture’s eight raised katakana.
The font adds 26 documented PUA positions; voiced forms and YI/YE use combining
dakuten wherever possible. [Input and mapping notes](research/okinawan.md) explain
the keyboard and [shared registry](data/okinawan/mappings.json).

[Try the font](https://genzui.mkpo.li/serif) ·
[Design gallery](https://genzui.mkpo.li/gallery) ·
[Download TTF](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf) ·
[Releases](https://github.com/mkpoli/GenZui/releases)

**GenZui Sans / 源萃ゴシック** is the gothic companion, built on Noto Sans JP
with the same historical repertoire. Version **0.101** contains **17,070 encoded
characters**. [Try GenZui Sans](https://genzui.mkpo.li/sans) ·
[Download TTF](https://genzui.mkpo.li/downloads/GenZuiSans-Regular.ttf) ·
[Build notes](research/genzui-sans.md)

## Download and use

- **Desktop:** [GenZuiSerif-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf).
  Open the file and select **Install**, then choose **GenZui Serif / 源萃明朝** in your app.
- **Complete package:** [version 0.114 ZIP](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular-0.114.zip),
  with TTF, WOFF2, an offline specimen, installation instructions and licences.
- **Web:** load the versioned stylesheet and set the font family:

```html
<link rel="stylesheet" href="https://genzui.mkpo.li/v0.114/genzui.css">
```

```css
body {
  font-family: "GenZui Serif", serif;
}
```

The font is free for personal and commercial use under [SIL OFL 1.1](OFL.txt).
Installing it makes it available to apps; browser fallback depends on the website
and browser settings. [Browser setup](browser/README.md) covers historical-kana fallback.

## Character coverage

- 286 hentaigana, with outlines from Noto Serif Hentaigana.
- All seven Unicode 18.0 kana additions: 𛄣 𛄤 𛄥 𛄦 𛄧 𛄨 𛅨.
- Ten encoded kana ligatures, including 𪜈 TOMO, 𬻿 katakana NARI,
  𬼀 SHITE and 𬼂 hiragana NARI.
- Small kana, the 16 Katakana Phonetic Extensions used for Ainu, and older kana forms.
- 13 Minnan tone letters, with overline and dot-below support.
- 27 Funatsu Okinawan forms and eight raised katakana, using 26 PUA bases and standard combining sequences.

The font covers every assigned character in Unicode 18.0's Hiragana, Katakana,
Katakana Phonetic Extensions, Kana Supplement, Kana Extended-A, Kana Extended-B
and Small Kana Extension blocks. A broader check of the Hiragana/Katakana script
properties and script extensions covers **all 763 characters**, including halfwidth kana, enclosed kana, squared
katakana and shared marks. Version 0.112 fills the last gap, **㌬ U+332C SQUARE PAATU**,
using native Noto squared-katakana components in horizontal and vertical forms.
See the [coverage audit](research/kana-coverage-0.114.json).
This is an encoding check; historical variants and arbitrary combining-mark
sequences need separate typographic assessment.

Shared ideographs retain Japanese regional forms. Chinese and Korean coverage
follows the Noto Serif JP base, with 卄 from Noto Serif CJK JP. Regular is the available weight.

### Two WU forms

𛄟 U+1B11F has a curved descent by default. OpenType stylistic set 1 (`ss01`,
“Hooked WU”) selects the hooked alternate without changing the character encoding.

```css
.hooked-wu {
  font-feature-settings: "ss01" 1;
}
```

The [Minnan specimen](https://genzui.mkpo.li/minnan) demonstrates tone placement,
combining marks, ruby and both WU forms. Vertical tone placement supports one to
four fullwidth kana at default advance and zero letter spacing; longer groups
or custom spacing require application-level positioning.

## Sources

| Source | Contribution |
| --- | --- |
| [Noto Serif JP](https://github.com/google/fonts/tree/main/ofl/notoserifjp) | Japanese subset of Noto Serif CJK; 16,726 encoded characters and kana components |
| [Noto Serif Hentaigana](https://github.com/notofonts/hentaigana) | 286 hentaigana and four other historical forms |
| [FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana) | 13 Minnan tone letters and two combining marks |
| [Noto Serif CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Serif) | 卄 (twenty), absent from the JP subset, from the same family’s full CJK font with Japanese default forms |
| [GenZui constructions](https://genzui.mkpo.li/?source=genzui#characters) | 21 historical kana constructions, SQUARE PAATU, ten transcription symbols and 26 Okinawan PUA characters, from Noto components and original drawing |

The [design gallery](https://genzui.mkpo.li/gallery) shows GenZui's constructions
in horizontal and vertical text. [Research notes](research/refinements-0.111.md)
record glyph references and construction details. The [font survey](research/existing-fonts.md)
covers other hentaigana fonts, including GenSeki Hentaigana Gothic.

Related project: **[Kureedo / クレード](https://kureedo.mkpo.li/)**, a Klee One
derivative with historical katakana and Ainu kana.

## Build the font

GenZui Sans has a separate [build guide](research/genzui-sans.md); it uses
Noto Sans JP, Noto Sans Hentaigana and GenSeki Hentaigana Gothic, and its
outputs go to `build/sans/`.

Python 3.12 is supported. Source fonts and Unicode data are pinned by URL and
SHA-256 in `sources/manifest.json`; they are downloaded by `sources.py`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/sources.py
.venv/bin/python scripts/repertoire.py
.venv/bin/python scripts/serif.py
.venv/bin/python scripts/check_serif.py
node scripts/check_okinawan_input.cjs
```

Outputs are in `build/serif/`. The checks cover 340 historical characters and transcription symbols, preservation of upstream glyphs and metrics, Japanese layout,
vertical small kana, combining marks, Minnan tones, WU variants, the 35 Okinawan forms and TTF/WOFF2 parity.
The historical glyph constructions are in `scripts/serif_forms.py`; squared kana
are in `scripts/compatibility.py`; Okinawan drawings are in `scripts/okinawan.py`; transcription additions are in `scripts/honkoku.py`. `scripts/check_coverage.py` checks the pinned
Unicode Script and Script_Extensions properties as part of font validation.

Release packaging uses `scripts/package_serif.py`. It requires passing Chrome,
Vivaldi and Firefox reports for the exact font bytes. The published ZIP already
contains those reports and the font validation results.

## Build the specimen website

After building and checking the font above, package it with the matching browser
report. The packager verifies the TTF and WOFF2 hashes against that report; a
modified font requires new browser validation.

```sh
cp research/browser-checks-0.114.json build/serif/browser-checks.json
.venv/bin/python scripts/package_serif.py
bun install --frozen-lockfile
bun run release:build
.venv/bin/python scripts/check_release.py
```

The public site is generated in `build/release/`. It also needs the checked
Sans package (`dist/GenZuiSans-Regular-0.101.zip` with its checks in `build/sans/`),
which supplies the `/sans` page and its downloads. Edit `site/`, `templates/` and
`scripts/release_site.py`. `build/site/` contains the offline development specimen
with glyph comparisons; the public gallery shows the released forms.
[Deployment notes](release/README.md) describe the Cloudflare configuration.

## Licences and credits

- **Font outlines and font binaries:** [SIL OFL 1.1](OFL.txt).
- **Project scripts and installer:** [MIT](LICENSE-scripts.txt).
- **Unicode data:** [Unicode licence](sources/Unicode-LICENSE.txt).
- **Historical comparison material from Jigmo:** CC0 1.0; see
  [Jigmo's licence](sources/upstream/Jigmo/LICENSE.txt).
- **Historical printed specimens:** public-domain scans, with
  [bibliographic references](research/specimens/README.md).

[NOTICE.txt](NOTICE.txt) credits the source projects. Original notices accompany
the fonts and remain under `sources/upstream/`. Jigmo supplied the NARI outline
in comparison fonts through 0.102; the released NARI is a GenZui drawing.
Further details are in the [licensing notes](research/licensing.md).
