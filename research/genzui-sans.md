# GenZui Sans

GenZui Sans / 源萃ゴシック is a Japanese sans-serif with historical kana.
Version 0.102 contains 17,070 encoded characters in Regular and Bold: the
repertoire of GenZui Serif 0.113 on the Noto Sans JP base. The experimental
Okinawan forms and historical katakana variants are not part of the Sans family.

## Sources

| Source | Regular | Bold | Contribution |
| --- | --- | --- | --- |
| Noto Sans JP | weight 400 | weight 700 | 16,732 encoded characters, with the original outlines, metrics and Japanese layout |
| Noto Sans Hentaigana | instance at axis 380 | instance at axis 720 | 286 hentaigana |
| Noto Sans Hentaigana | Regular instance | instance at axis 780 | Four archaic kana: 𛀀 𛄠 𛄡 𛄢 |
| GenSeki Hentaigana Gothic 1.201 | Regular | Bold | 21 historical kana, small kana and ligatures |
| Noto Sans CJK JP | Regular | Bold | U+5344 卄 |
| FRB Taiwanese Kana | outlines | blend toward GenZui Bold masters | 13 Minnan tone letters and two combining marks |
| GenZui | drawings | Bold masters | Squared PAATU and the transcription symbols |

The Noto Sans Hentaigana instances are compiled from the Glyphs package at
upstream commit `3aa4d30ee04254d3d0a69c500de7fda494e3b302`. The unencoded
archaic E and YE drawings receive U+1B000 and U+1B001.

## Weight

Upstream gives the Noto Sans Hentaigana Regular instance (axis 400) weight
class 500. Beside Noto Sans JP Regular its hentaigana read darker than the
surrounding kana: their median stem is 73 units against 69 for hiragana.
Version 0.100 used the DemiLight instance (axis 300, stem 58), which reads
too thin. Version 0.101 adds an instance at axis 380 to the upstream sources,
where the hentaigana's median stem is 69.5 units against 69.3 for the
hiragana; the check requires the two to stay within two units. The four
archaic kana are simple katakana-like forms and keep the Regular instance,
matching ordinary katakana stems of 72–75 units. The stem estimate is twice
the filled area over the perimeter, the median over the set.

Bold applies the same rule to Noto Sans JP Bold. Upstream's Bold instance
(axis 700) gives the hentaigana a median stem of 106.0 units against 108.5 for
the Bold hiragana; axis 720 gives 108.3. The archaic kana use axis 780, where
their median stem is 114.1 against 114.3 for the Bold katakana. The checks
hold both pairs within two units in each face.

## Refits

Three GenSeki outlines sit outside the range of their kana peers. Each is
scaled about its centre and, where scaled, eroded back to the donor's stem
width so it grows without getting heavier (`scripts/sans_forms.py`):

| Character | Change |
| --- | --- |
| 𛄣 U+1B123 KOTO | Body raised from 723 to 802 units, the range of 𛄤 TOKI, 𛄥 TOTE and 𪜈 TOMO |
| 𛄧 U+1B127 alternate NE | Body raised from 728 to 768 units, matching the katakana cap height |
| 𛅨 U+1B168 small archaic YE | Lowered 30 units onto the small-kana baseline |

GenSeki's Bold drawings have the same proportions and get the same fits:
KOTO 733 → 807 units (scale 1.12, eroded 7), alternate NE 735 → 813 units
(scale 1.125, eroded 7), small YE lowered 30 units.

The other eighteen GenSeki outlines and all Noto outlines are unchanged, which
the checks verify against the compiled instances.

## Bold drawings

GenZui's own outlines in Bold, measured by the weight gain over Regular
against Noto Sans JP's kana (1.47–1.62, median 1.53):

- **Minnan tone letters:** the FRB outlines blended 0.76 toward the Bold
  masters drawn for GenZui Serif (`data/minnan/bold.json`), which share their
  points. The blend's median gain is 1.53; the full Serif masters gain 1.66.
  The overline and dot keep Regular's clearance from the kana.
- **Transcription symbols:** Noto Sans JP Bold's dashed frame has 37-unit
  strokes against 31 in Regular. The minus takes the frame's stroke, and the
  half-turn arrow keeps its outer edge while its ring and barbs gain 6–7 units
  inward (`scripts/sans_forms.py`).
- **Dakuten after historical kana:** the Bold handakuten is 31 units wider and
  reaches 16 units lower; the marks keep Regular's right edge and clearance.

## Build

Use a separate environment: the instance compiler requires a newer fontTools
than the Serif environment.

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

Outputs are in `build/sans/`: `GenZuiSans-Regular` and `GenZuiSans-Bold` as TTF
and WOFF2, an offline specimen `index.html`, `preview.png` and a hentaigana
contact sheet.
Source fetching and instance compilation are part of the build; verified
archives and the compiled instances are cached under `build/sans-work/`.

The checks run on each face against the Noto Sans JP instance of its weight.
They compare every Noto Sans JP outline and metric with the base font,
exercise Japanese layout in both writing directions, verify historical marks,
Minnan tone placement, check the refits, and
compare TTF with WOFF2. The coverage audit requires all 763 characters in
Unicode 18's Hiragana/Katakana scripts and script extensions. The browser check
validates the offline specimen in Chromium and Firefox, compares TTF and WOFF2
rasters for both faces and records their hashes; the packager rejects stale
hashes and writes `dist/GenZuiSans-0.102.zip`.

## Site

`scripts/sans_site.py` renders `templates/sans.html` for the development
specimen (`build/site/sans.html`, embedded fonts) and the public site
(`/sans`, fonts from `/sans-v0.101/`). The public build also publishes the
downloads, `/genzui-sans.css`, the social card and the announcement texts.
Version reports live in `research/sans-browser-checks-0.101.json` and
`research/sans-kana-coverage-0.101.json`.
