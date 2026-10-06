# 源萃 GenZui

GenZui (源萃, げんずい) is a Japanese type family with hentaigana, historical
kana and Unicode 18.0 additions.

| | 源萃明朝 GenZui Serif | 源萃ゴシック GenZui Sans |
| --- | --- | --- |
| Style | Japanese serif on Noto Serif JP | Japanese sans-serif on Noto Sans JP |
| Release | Regular and Bold 0.118 · 17,271 characters | Regular and Bold 0.103 · 17,251 characters |
| Specimen | [genzui.mkpo.li/serif](https://genzui.mkpo.li/serif) | [genzui.mkpo.li/sans](https://genzui.mkpo.li/sans) |
| TTF | [GenZuiSerif-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Regular.ttf) · [GenZuiSerif-Bold.ttf](https://genzui.mkpo.li/downloads/GenZuiSerif-Bold.ttf) | [GenZuiSans-Regular.ttf](https://genzui.mkpo.li/downloads/GenZuiSans-Regular.ttf) · [GenZuiSans-Bold.ttf](https://genzui.mkpo.li/downloads/GenZuiSans-Bold.ttf) |
| Package | [ZIP](https://genzui.mkpo.li/downloads/GenZuiSerif-0.118.zip) | [ZIP](https://genzui.mkpo.li/downloads/GenZuiSans-0.103.zip) |

[Home](https://genzui.mkpo.li/) ·
[Design gallery](https://genzui.mkpo.li/gallery) ·
[Font comparison](https://genzui.mkpo.li/compare) ·
[Releases](https://github.com/mkpoli/GenZui/releases)

## Download and use

Both fonts are free for personal and commercial use under
[SIL OFL 1.1](OFL.txt). Open the TTF and select **Install**, then choose
**GenZui Serif / 源萃明朝** or **GenZui Sans / 源萃ゴシック** in your app.
Each complete package adds WOFF2, an offline specimen, installation
instructions and licences. The two fonts install side by side.

For rare kanji, **GenZui Sans Han / 源萃ゴシック漢字** is a separate
download: two Regular files that add every CJK ideograph, radical and stroke in
Unicode 18 that GenZui Sans lacks. Install them beside GenZui Sans and list
GenZui Sans first. See [GenZui Sans Han](#genzui-sans-han) for its sources.

Browser fallback depends on the website and browser settings.
[Browser setup](browser/README.md) covers historical-kana fallback.

### On the web

```html
<link rel="stylesheet" href="https://genzui.mkpo.li/v0.118/genzui.css">
<link rel="stylesheet" href="https://genzui.mkpo.li/sans-v0.103/genzui-sans.css">
```

```css
.serif-sample { font-family: "GenZui Serif", serif; }
.sans-sample  { font-family: "GenZui Sans", sans-serif; }
```

With GenZui Sans Han, load its `genzui-sans-han.css` after the Sans stylesheet
and add the family after GenZui Sans. Each file declares its `unicode-range`, so
a browser fetches it only for pages that use its characters:

```css
.sans-sample  { font-family: "GenZui Sans", "GenZui Sans Han", sans-serif; }
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
[Serif 0.118](research/kana-coverage-0.118.json) ·
[Sans 0.103](research/sans-kana-coverage-0.103.json). These are encoding
checks; historical variants and arbitrary combining-mark sequences need
separate typographic assessment.

Shared ideographs keep Japanese regional forms. Chinese and Korean coverage
follows each face’s Noto base, with 卄 from the matching Noto CJK font.
Both families have Regular and Bold.

### GenZui Serif additions

- 27 Funatsu Okinawan forms and eight raised katakana, on 26 documented PUA
  bases. Voiced forms and YI/YE use combining dakuten wherever possible. The
  [Okinawan composer](https://genzui.mkpo.li/serif#okinawan) on the Serif page,
  the [input notes](research/okinawan.md) and the
  [mapping registry](data/okinawan/mappings.json) document the keyboard.
- 21 historical kana constructions from Noto components and original drawing.

### 구결자

181 of the 255 구결자 that 한/글 places at U+F67E–U+F77C are drawn from each
Serif face's own glyph of the ideograph they reproduce; the other 74 are not yet
drawn. Published Sans 0.103 does not include these forms. PUA assignments need a matching font on the reading side. The
registry is [data/gugyeol/forms.json](data/gugyeol/forms.json).

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
| [Noto Serif CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Serif) | 卄 (twenty), absent from the JP subset, from the same family’s full CJK font with Japanese default forms; also the twin ideograph for 6 of the 181 drawn 구결자, where the twin is absent from Noto Serif JP |
| [GenZui constructions](https://genzui.mkpo.li/serif?source=genzui#characters) | 21 historical kana constructions, SQUARE PAATU, ten transcription symbols and 26 Okinawan PUA characters, from Noto components and original drawing |
| [구결 registry](data/gugyeol/forms.json) | 181 구결자, each drawn from the face’s own glyph of its twin ideograph, or from Noto Serif CJK JP where that twin is absent |

### GenZui Sans

| Source | Contribution |
| --- | --- |
| [Noto Sans JP](https://github.com/google/fonts/tree/main/ofl/notosansjp), weights 400 and 700 | 16,732 encoded characters, with the original outlines, metrics and Japanese layout |
| [Noto Sans Hentaigana](https://github.com/notofonts/hentaigana) | 286 hentaigana from stem-matched instances at weight axis 380 (Regular) and 720 (Bold), and four archaic kana from the Regular instance and axis 780 (Bold). The unreleased sans companion of Noto Serif Hentaigana, designed by Kazuhiro Yamada (nipponia) and compiled here from source |
| [GenSeki Hentaigana Gothic](https://github.com/MihailJP/GenSekiHentaiganaGothic) 1.201 Regular and Bold | 20 historical kana, small kana and ligatures. Its README credits 𛄣 𛄤 𛄥 𛄦 and the ligatures 𪜈 𬻿 𬼀 𬼂 to [Sukima Gothic](https://booth.pm/ja/items/2117070); its name record credits the other kana to [GenSeki Gothic](https://github.com/ButTaiwan/genseki-font) |
| [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Sans) Regular and Bold | U+5344 卄 |
| [FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana) | 13 Minnan tone letters and two combining marks; Bold blends them toward GenZui’s Bold masters |
| GenZui constructions | Alternate WI 𛄨 from Noto Sans JP strokes, squared PAATU and the transcription symbols |

### GenZui Sans Han

A separate download that fills in every CJK ideograph GenZui Sans lacks.
Each character takes the first source that has it.

| Source | Contribution |
| --- | --- |
| [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk/tree/main/Sans) Regular | 16,546 ideographs in the Source Han Sans design, Japanese forms |
| [Sukima Gothic](https://booth.pm/ja/items/2117070) 11.41 Main and Sub | 37,005 ideographs, Japanese forms on the Genshin Gothic / Source Han Sans 1.002 base |
| [Plangothic](https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project) P1 and P2 2.9.5795 | 35,703 characters, mostly extension ideographs, on Source Han Sans CN, Chinese Mainland forms |

The [design gallery](https://genzui.mkpo.li/gallery) shows GenZui’s own
constructions in horizontal and vertical text. [Research notes](research/refinements-0.111.md)
record glyph references and construction details. The [font survey](research/existing-fonts.md)
covers other hentaigana fonts, including GenSeki Hentaigana Gothic.
[GenZui Sans](research/genzui-sans.md) records its stem matching, refits and a
provenance check of the hentaigana. The [Sans specimen](https://genzui.mkpo.li/sans#sources)
traces each source back to the fonts it came from.

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

### GenZui Serif Okinawan / 源萃明朝 沖縄文字

A sentence-ready subset of GenZui Serif: 27 Funatsu forms, eight raised katakana,
ordinary kana, Latin letters, numbers and punctuation. Regular and Bold have
805 encoded characters with the full family’s outlines, metrics and shaping.
The complete GenZui Serif fonts include the same Okinawan forms.

```sh
.venv/bin/python scripts/okinawan_subset.py
.venv/bin/python scripts/check_okinawan_subset.py
.venv/bin/python scripts/okinawan_subset.py --package
```

Outputs are in `build/okinawan/`; `index.html` contains editable sentences.
The separate package is `dist/GenZuiSerifOkinawan-0.118.zip`.

### GenZui Sans

```sh
python3 -m venv .venv-sans
.venv-sans/bin/python -m pip install -r requirements-sans.lock
.venv-sans/bin/python scripts/sans.py
.venv-sans/bin/python scripts/sans_bold.py
.venv-sans/bin/python scripts/check_sans.py
.venv-sans/bin/python scripts/check_sans_bold.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/check_sans_browser.cjs
.venv-sans/bin/python scripts/package_sans.py
```

Outputs are in `build/sans/`. The [build guide](research/genzui-sans.md)
covers the stem-matched hentaigana instances, the GenSeki refits, the Bold
drawings, the browser check and packaging to `dist/`.

The Sans Okinawan candidate build provides matching Regular/Bold sentence-ready
subsets and extends the published full Sans repertoire. See its
[build and proof guide](research/sans-okinawan.md).

GenZui Sans P / 源萃ゴシックP is derived from the built Sans faces. It applies
the font's `palt` widths by default for applications that ignore the feature
and is packaged separately:

```sh
.venv-sans/bin/python scripts/sans_p.py
.venv-sans/bin/python scripts/check_sans_p.py
.venv-sans/bin/python scripts/package_sans_p.py
```

It writes `build/sans/GenZuiSansP-*` and `dist/GenZuiSansP-0.103.zip`.

### GenZui Sans Han

Build GenZui Sans Regular first. Sukima Gothic is downloaded from BOOTH with a
signed-in account; place `sukima-gothic_ver11.41.zip` in `build/sans-work/han/`.
The other sources are fetched and checked against `sources/han-manifest.json`.

```sh
.venv-sans/bin/python scripts/sans_han.py
.venv-sans/bin/python scripts/check_sans_han.py
.venv-sans/bin/python scripts/package_sans_han.py
```

Outputs are in `build/sans-han/`; the package is `dist/GenZuiSansHan-0.100.zip`.
The [Han notes](research/genzui-sans-han.md) describe the source order and the
file split.

### GenZui Serif Kugyol and GenZui Sans Kugyol

GenZui Serif Kugyol and GenZui Sans Kugyol are cut from the built Serif and
Sans faces to exactly the 181 구결자 those faces draw at U+F67E–U+F77C, plus
SPACE and IDEOGRAPHIC SPACE. Outlines, metrics, and licensing metadata match
the parent face; only the repertoire is reduced. Use them as a compact 구결
fallback font where the full GenZui faces are unnecessary.

```sh
.venv/bin/python scripts/kugyol.py
.venv/bin/python scripts/check_kugyol.py
```

Both parents must be built from the current sources with all 181 forms. The published Sans 0.103 fonts predate this repertoire and cannot serve as the Sans Kugyol parent. Outputs, including a
contact-sheet `proof.png`, are in `build/kugyol/`.

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

### Font comparison page

`/compare` sets GenZui beside other kana and hentaigana fonts. The fonts are
pinned in `sources/compare-manifest.json`; Sukima Gothic needs a BOOTH login, so
pass a local copy of its archive. Measuring is a separate step; the page build
reads only the committed results. Other fonts are not shipped on the site: their
glyphs appear as images rendered from the pinned files, in
`research/font-comparison-images/`, with each font's credit beside them.

```sh
.venv/bin/python scripts/compare_sources.py --sukima PATH/sukima-gothic_ver11.41.zip
.venv/bin/python scripts/compare_fonts.py   # writes research/font-comparison*.json
.venv/bin/python scripts/compare_site.py    # writes build/site/compare.html
```

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
