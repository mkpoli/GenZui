# 源萃明朝 GenZui Serif

GenZui (源萃, げんずい) is a Japanese Mincho font derived from **Noto Serif JP**,
**Noto Serif Hentaigana** and **FRB Taiwanese Kana**, with drawn historical kana
and Unicode 18.0 additions. Version **0.111** contains **17,052 encoded characters**
in one Regular weight.

[Try the font](https://genzui.mkpo.li/) ·
[Design gallery](https://genzui.mkpo.li/gallery) ·
[Download TTF](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf) ·
[Releases](https://github.com/mkpoli/GenZui/releases)

## Download and use

- **Desktop:** [GenZuiSerif-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf).
  Open the file and select **Install**, then choose **GenZui Serif / 源萃明朝** in your app.
- **Complete package:** [version 0.111 ZIP](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular-0.111.zip),
  with TTF, WOFF2, an offline specimen, installation instructions and licences.
- **Web:** load the versioned stylesheet and set the font family:

```html
<link rel="stylesheet" href="https://genzui.mkpo.li/v0.111/genzui.css">
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

The font covers every assigned character in Unicode 18.0's Hiragana, Katakana,
Katakana Phonetic Extensions, Kana Supplement, Kana Extended-A, Kana Extended-B
and Small Kana Extension blocks. A broader check of the Hiragana/Katakana script
properties and script extensions covers **762 of 763 characters**; the missing
character is **㌬ U+332C SQUARE PAATU**. See the [coverage audit](research/kana-coverage-0.111.json).
This is an encoding check; historical variants and arbitrary combining-mark
sequences need separate typographic assessment.

Shared ideographs retain Japanese regional forms. Chinese and Korean coverage
is limited to the Noto Serif JP base. Regular is the available weight.

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
| [Noto Serif JP](https://github.com/google/fonts/tree/main/ofl/notoserifjp) | Japanese base and kana components; 16,726 encoded characters |
| [Noto Serif Hentaigana](https://github.com/notofonts/hentaigana) | 286 hentaigana and four other historical forms |
| [FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana) | 13 Minnan tone letters and two combining marks |
| GenZui | 21 constructions from Noto components and original drawing |

The [design gallery](https://genzui.mkpo.li/gallery) shows GenZui's constructions
in horizontal and vertical text. [Research notes](research/refinements-0.111.md)
record glyph references and construction details. The [font survey](research/existing-fonts.md)
covers other hentaigana fonts, including GenSeki Hentaigana Gothic.

Related project: **[Kureedo / クレード](https://kureedo.mkpo.li/)**, a Klee One
derivative with historical katakana and Ainu kana.

## Build the font

Python 3.12 is supported. Source fonts and Unicode data are pinned by URL and
SHA-256 in `sources/manifest.json`; they are downloaded by `sources.py`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/sources.py
.venv/bin/python scripts/repertoire.py
.venv/bin/python scripts/serif.py
.venv/bin/python scripts/check_serif.py
```

Outputs are in `build/serif/`. The checks cover the 328 historical characters and
support marks, preservation of upstream glyphs and metrics, Japanese layout,
vertical small kana, combining marks, Minnan tones, WU variants and TTF/WOFF2 parity.
The historical glyph constructions are in `scripts/serif_forms.py`.

Release packaging uses `scripts/package_serif.py`. It requires passing Chrome,
Vivaldi and Firefox reports for the exact font bytes. The published ZIP already
contains those reports and the font validation results.

## Build the specimen website

To use the published font for site development, prepare the Python environment
and download the pinned sources as above, then extract the checked release:

```sh
.venv/bin/python -m zipfile -e releases/v0.111/GenZuiSerif-Regular-0.111.zip build/serif
mkdir -p dist
cp releases/v0.111/GenZuiSerif-Regular-0.111.zip dist/
bun install --frozen-lockfile
bun run release:build
.venv/bin/python scripts/check_release.py
```

The public site is generated in `build/release/`. Edit `site/`, `templates/` and
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
