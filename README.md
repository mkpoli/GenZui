# 源萃 GenZui

GenZui (源萃, げんずい) is a Japanese type family with hentaigana, historical
kana and Unicode 18.0 additions.

| | 源萃明朝 GenZui Serif | 源萃ゴシック GenZui Sans |
| --- | --- | --- |
| Style | Japanese serif on Noto Serif JP | Japanese sans-serif on Noto Sans JP |
| Release | Regular and Bold 0.117 · 17,090 characters | Regular 0.101 · 17,070 characters |
| Specimen | [genzui.mkpo.li/serif](https://genzui.mkpo.li/serif) | [genzui.mkpo.li/sans](https://genzui.mkpo.li/sans) |
| TTF | [GenZuiSerif-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf) · [GenZuiSerif-Bold.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Bold.ttf) | [GenZuiSans-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSans-Regular.ttf) |
| Package | [ZIP](https://genzui.mkpo.li/downloads/GenZuiSerif-0.117.zip) | [ZIP](https://genzui.mkpo.li/downloads/GenZuiSans-Regular-0.101.zip) |

[Home](https://genzui.mkpo.li/) ·
[Design gallery](https://genzui.mkpo.li/gallery) ·
[Releases](https://github.com/mkpoli/GenZui/releases)

## Download and use

Both fonts are free for personal and commercial use under
[SIL OFL 1.1](OFL.txt). Open the TTF and select **Install**, then choose
**GenZui Serif / 源萃明朝** or **GenZui Sans / 源萃ゴシック** in your app.
Each complete package adds WOFF2, an offline specimen, installation
instructions and licences. The two fonts install side by side.

Browser fallback depends on the website and browser settings.
[Browser setup](browser/README.md) covers historical-kana fallback.

### On the web

```html
<link rel="stylesheet" href="https://genzui.mkpo.li/v0.117/genzui.css">
<link rel="stylesheet" href="https://genzui.mkpo.li/sans-v0.101/genzui-sans.css">
```

```css
.serif-sample { font-family: "GenZui Serif", serif; }
.sans-sample  { font-family: "GenZui Sans", sans-serif; }
```

## Character coverage

Both faces include:

- 286 hentaigana.
- All seven Unicode 18.0 kana additions: 𛄣 𛄤 𛄥 𛄦 𛄧 𛄨 𛅨.
- Ten encoded kana ligatures, including 𪜈 TOMO, 𬻿 katakana NARI,
  𬼀 SHITE and 𬼂 hiragana NARI.
  Type them as their own characters; ordinary kana sequences are never
  rewritten into ligatures, because those depend on the word and the hand.
- Small kana, the 16 Katakana Phonetic Extensions used for Ainu, and older kana forms.
- 13 Minnan tone letters, with overline and dot-below support.

The [Minnan specimen](https://genzui.mkpo.li/minnan) shows tone placement,
combining marks, ruby and both WU forms. Vertical tone placement supports one
to four fullwidth kana at default advance and zero letter spacing; longer
groups or custom spacing need application-level positioning.

Every assigned character in Unicode 18.0’s Hiragana, Katakana, Katakana Phonetic
Extensions, Kana Supplement, Kana Extended-A, Kana Extended-B and Small Kana
Extension blocks is present. The Hiragana and Katakana script properties and
script extensions together cover **all 763 characters**, including halfwidth
kana, enclosed kana, squared katakana and shared marks. Audits:
[Serif 0.117](research/kana-coverage-0.117.json) ·
[Sans 0.101](research/sans-kana-coverage-0.101.json). These are encoding
checks; historical variants and arbitrary combining-mark sequences need
separate typographic assessment.

Shared ideographs keep Japanese regional forms. Chinese and Korean coverage
follows each face’s Noto base, with 卄 from the matching Noto CJK font.
GenZui Serif has Regular and Bold; GenZui Sans is Regular only.

### GenZui Serif additions

- 27 Funatsu Okinawan forms and eight raised katakana, on 26 documented PUA
  bases. Voiced forms and YI/YE use combining dakuten wherever possible. The
  [Okinawan composer](https://genzui.mkpo.li/serif#okinawan) on the Serif page,
  the [input notes](research/okinawan.md) and the
  [mapping registry](data/okinawan/mappings.json) document the keyboard.
- 21 historical kana constructions from Noto components and original drawing.

### Hooked WU

In GenZui Serif, 𛄟 U+1B11F has a curved descent by default. Stylistic set 1
(`ss01`, “Hooked WU”) selects the hooked alternate without changing the
character encoding.

```css
.hooked-wu {
  font-feature-settings: "ss01" 1;
}
```

## Sources

### GenZui Serif

| Source | Contribution |
| --- | --- |
| [Noto Serif JP](https://github.com/google/fonts/tree/main/ofl/notoserifjp) | Japanese subset of Noto Serif CJK; 16,726 encoded characters and kana components |
| [Noto Serif Hentaigana](https://github.com/notofonts/hentaigana) | 286 hentaigana and four other historical forms |
| [FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana) | 13 Minnan tone letters and two combining marks |
| [Noto Serif CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Serif) | 卄 (twenty), absent from the JP subset, from the same family’s full CJK font with Japanese default forms |
| [GenZui constructions](https://genzui.mkpo.li/serif?source=genzui#characters) | 21 historical kana constructions, SQUARE PAATU, ten transcription symbols and 26 Okinawan PUA characters, from Noto components and original drawing |

### GenZui Sans

| Source | Contribution |
| --- | --- |
| [Noto Sans JP](https://github.com/google/fonts/tree/main/ofl/notosansjp), weight 400 | 16,732 encoded characters, with the original outlines, metrics and Japanese layout |
| [Noto Sans Hentaigana](https://github.com/notofonts/hentaigana) | 286 hentaigana from a stem-matched instance at weight axis 380, and four archaic kana from the Regular instance |
| [GenSeki Hentaigana Gothic](https://github.com/MihailJP/GenSekiHentaiganaGothic) 1.201 Regular | 21 historical kana, small kana and ligatures |
| [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Sans) Regular | U+5344 卄 |
| [FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana) | 13 Minnan tone letters and two combining marks |
| GenZui constructions | Squared PAATU and the transcription symbols |

The [design gallery](https://genzui.mkpo.li/gallery) shows GenZui’s own
constructions in horizontal and vertical text. [Research notes](research/refinements-0.111.md)
record glyph references and construction details. The [font survey](research/existing-fonts.md)
covers other hentaigana fonts, including GenSeki Hentaigana Gothic.
[GenZui Sans](research/genzui-sans.md) records its stem matching and refits.

Related project: **[Kureedo / クレード](https://kureedo.mkpo.li/)**, a Klee One
derivative with historical katakana and Ainu kana.

## Build the fonts

Python 3.12 is supported. Source fonts and Unicode data are pinned by URL and
SHA-256 in `sources/manifest.json` and `sources/sans-manifest.json`.
Each face has its own virtual environment; the Sans instance compiler needs a
newer fontTools than the Serif environment.

### GenZui Serif

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/sources.py
.venv/bin/python scripts/repertoire.py
.venv/bin/python scripts/serif.py
.venv/bin/python scripts/check_serif.py
.venv/bin/python scripts/bold.py
.venv/bin/python scripts/check_bold.py
node scripts/check_okinawan_input.cjs
.venv/bin/python scripts/check_serif_browsers.py
.venv/bin/python scripts/package_serif.py
```

Outputs are in `build/serif/`. The checks cover the historical and
transcription inventory, preservation of upstream glyphs and metrics, Japanese
layout, marks, Minnan tones, WU variants, the Okinawan forms and TTF/WOFF2
parity. `scripts/check_coverage.py` checks the pinned Unicode Script and
Script_Extensions properties. `scripts/check_serif_browsers.py` runs from WSL
and checks both faces in headless Windows Chrome, Vivaldi and Firefox, whose
paths it reads from `~/.config/genzui/windows-browsers.json`
(`{"chrome.exe": {"path": "C:\\..."}, "vivaldi.exe": {...}, "firefox.exe": {...}}`).
Release packaging requires that report for the exact font bytes, then writes
the ZIP.

### GenZui Sans

```sh
python3 -m venv .venv-sans
.venv-sans/bin/python -m pip install -r requirements-sans.lock
.venv-sans/bin/python scripts/sans.py
.venv-sans/bin/python scripts/check_sans.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/check_sans_browser.cjs
.venv-sans/bin/python scripts/package_sans.py
```

Outputs are in `build/sans/`. The [build guide](research/genzui-sans.md)
covers the stem-matched hentaigana instance, the GenSeki refits, the browser
check and packaging to `dist/`.

## Build the specimen website

After both faces are packaged, generate the public site:

```sh
bun install --frozen-lockfile
bun run release:build
.venv/bin/python scripts/check_release.py
```

The public site is written to `build/release/` and serves a family landing at
`/`, GenZui Serif at `/serif` and GenZui Sans at `/sans`, with fonts from the
versioned release folders. Edit `site/`, `templates/` and
`scripts/release_site.py` / `scripts/sans_site.py`.
`build/site/` holds the offline development specimen with glyph comparisons.
[Deployment notes](release/README.md) describe the Cloudflare configuration.

## Licences and credits

- **Font outlines and font binaries:** [SIL OFL 1.1](OFL.txt).
- **Project scripts and installer:** [MIT](LICENSE-scripts.txt).
- **Unicode data:** [Unicode licence](sources/Unicode-LICENSE.txt).
- **Historical comparison material from Jigmo:** CC0 1.0; see
  [Jigmo's licence](sources/upstream/Jigmo/LICENSE.txt).
- **Historical printed specimens:** public-domain scans, with
  [bibliographic references](research/specimens/README.md).

[NOTICE.txt](NOTICE.txt) credits the source projects. Original notices
accompany the fonts and remain under `sources/upstream/`. Jigmo supplied the
NARI outline in comparison fonts through 0.102; the released NARI is a GenZui
drawing. Further details are in the [licensing notes](research/licensing.md).
