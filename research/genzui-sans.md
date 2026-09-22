# GenZui Sans Regular

GenZui Sans / 源萃ゴシック is a Japanese sans-serif with historical kana.
Version 0.100 contains 17,070 encoded characters in one Regular weight: the
repertoire of GenZui Serif 0.113 on the Noto Sans JP base. The experimental
Okinawan forms and historical katakana variants are not part of the Sans family.

## Sources

| Source | Contribution |
| --- | --- |
| Noto Sans JP, weight 400 | 16,732 encoded characters, with the original outlines, metrics and Japanese layout |
| Noto Sans Hentaigana, DemiLight instance | 286 hentaigana |
| Noto Sans Hentaigana, Regular instance | Four archaic kana: 𛀀 𛄠 𛄡 𛄢 |
| GenSeki Hentaigana Gothic 1.201 Regular | 21 historical kana, small kana and ligatures |
| Noto Sans CJK JP Regular | U+5344 卄 |
| FRB Taiwanese Kana | 13 Minnan tone letters and two combining marks |
| GenZui | Hooked WU, squared PAATU and the transcription symbols |

Both Noto Sans Hentaigana instances are compiled from the Glyphs package at
upstream commit `3aa4d30ee04254d3d0a69c500de7fda494e3b302`. The unencoded
archaic E and YE drawings receive U+1B000 and U+1B001.

## Weight

Upstream gives the Noto Sans Hentaigana Regular instance (axis 400) weight
class 500, and its DemiLight instance (axis 300) weight class 400. Beside Noto
Sans JP Regular the Regular-instance hentaigana read darker than the
surrounding kana: their median stem is 73 units against 69 for hiragana, and
the cursive forms carry more strokes in the same body. The DemiLight instance
(median stem 58) balances the text colour, so it supplies the 286 hentaigana.
The four archaic kana are simple katakana-like forms and keep the Regular
instance, matching ordinary katakana stems of 72–75 units.

## Refits

Three GenSeki outlines sit outside the range of their kana peers. Each is
scaled about its centre and, where scaled, eroded back to the donor's stem
width so it grows without getting heavier (`scripts/sans_forms.py`):

| Character | Change |
| --- | --- |
| 𛄣 U+1B123 KOTO | Body raised from 723 to 802 units, the range of 𛄤 TOKI, 𛄥 TOTE and 𪜈 TOMO |
| 𛄧 U+1B127 alternate NE | Body raised from 728 to 768 units, matching the katakana cap height |
| 𛅨 U+1B168 small archaic YE | Lowered 30 units onto the small-kana baseline |

The other eighteen GenSeki outlines and all Noto outlines are unchanged, which
the checks verify against the compiled instances.

## Build

Use a separate environment: the instance compiler requires a newer fontTools
than the Serif environment.

```sh
python3 -m venv .venv-sans
.venv-sans/bin/python -m pip install -r requirements-sans.lock
.venv-sans/bin/python scripts/sans.py
.venv-sans/bin/python scripts/check_sans.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright node scripts/check_sans_browser.cjs
.venv-sans/bin/python scripts/package_sans.py
```

Outputs are in `build/sans/`: `GenZuiSans-Regular.ttf`, `GenZuiSans-Regular.woff2`,
an offline specimen `index.html`, `preview.png` and a hentaigana contact sheet.
Source fetching and instance compilation are part of the build; verified
archives and the compiled instances are cached under `build/sans-work/`.

The checks compare every Noto Sans JP outline and metric with the base font,
exercise Japanese layout in both writing directions, verify historical marks,
Minnan tone placement and the Hooked WU alternate, check the refits, and
compare TTF with WOFF2. The coverage audit requires all 763 characters in
Unicode 18's Hiragana/Katakana scripts and script extensions. The browser check
validates the offline specimen in Chromium and Firefox and records the font
hashes; the packager rejects stale hashes and writes
`dist/GenZuiSans-Regular-0.100.zip`.

## Site

`scripts/sans_site.py` renders `templates/sans.html` for the development
specimen (`build/site/sans.html`, embedded fonts) and the public site
(`/sans`, fonts from `/sans-v0.100/`). The public build also publishes the
downloads, `/genzui-sans.css`, the social card and the announcement texts.
Version reports live in `research/sans-browser-checks-0.100.json` and
`research/sans-kana-coverage-0.100.json`.
