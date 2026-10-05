# GenZui Sans

GenZui Sans / 源萃ゴシック is a Japanese sans-serif with historical kana.
Version 0.103 contains 17,070 encoded characters in Regular and Bold: the
repertoire of GenZui Serif 0.113 on the Noto Sans JP base. The experimental
Okinawan forms and historical katakana variants are not part of the Sans family.

## Sources

| Source | Regular | Bold | Contribution |
| --- | --- | --- | --- |
| Noto Sans JP | weight 400 | weight 700 | 16,732 encoded characters, with the original outlines, metrics and Japanese layout |
| Noto Sans Hentaigana | instance at axis 380 | instance at axis 720 | 286 hentaigana |
| Noto Sans Hentaigana | Regular instance | instance at axis 780 | Four archaic kana: 𛀀 𛄠 𛄡 𛄢 |
| GenSeki Hentaigana Gothic 1.201 | Regular | Bold | 20 historical kana, small kana and ligatures |
| Noto Sans CJK JP | Regular | Bold | U+5344 卄 |
| GenZui | Noto Sans JP Regular strokes, drawings | Noto Sans JP Bold strokes, Bold masters | Alternate WI 𛄨, squared PAATU, the transcription symbols, 13 Minnan tone letters and two combining marks |

The Minnan forms keep the advances, mark anchors and overline width of
[FRB Taiwanese Kana](https://github.com/ctrlcctrlv/FRBTaiwaneseKana), whose
outlines GenZui Serif uses.

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
(axis 700) gives the hentaigana a median stem of 106.0 units against 108.6 for
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
KOTO 733 → 806 units (scale 1.12, eroded 7), alternate NE 735 → 813 units
(scale 1.125, eroded 7), small YE lowered 30 units.

The other seventeen GenSeki outlines and all Noto outlines are unchanged, which
the checks verify against the compiled instances.

## Alternate WI

GenSeki's 𛄨 is narrower and lower than the katakana around it. GenZui Sans
builds it like GenZui Serif's alternate WI, from Noto Sans JP's own strokes:
WI's two bars and right stem, with NA's falling stroke as the left descent.
NA's stroke is thinned about its centreline to the stem's width. The descent
moves 160 units left and its foot returns up to 67 units inward; the right stem
keeps WI's position; the upper bar drops 22 units and the lower bar rises 30,
as in Serif. Each weight applies the same moves to its own
strokes, so the letter keeps WI's height and bar width (`scripts/sans_forms.py`).

## Minnan tone letters

The 13 tone letters of Kana Extended-B and U+0305/U+0323 are drawn from Noto
Sans JP's strokes (`scripts/sans_minnan.py`). Their structure follows the
period samples reproduced in Fredrick R. Brennan's proposal
[L2/20-209R](https://www.unicode.org/L2/L2020/20209r-taiwan-kana.pdf)
(13 December 2020); page numbers are the proposal's printed pages, which
match the PDF:

- p. 18: Âng and Ogawa (1992), *Minnan Classic Dictionary Collection*,
  vol. 1 p. 3, the table of signs (符號), plain and nasalized (鼻音) tones;
- p. 18: the same work, vol. 1 p. 5, aspirated kana with the dot below;
- p. 19: vol. 1 p. 3, overlined kana in running text;
- p. 20: Hirasawa (1914), *Taiwan Proverb Collection*, p. 147, tones in
  vertical text;
- p. 21: Ogawa (1938), *New Japanese–Taiwanese Dictionary*, page not
  identified, reproduced from Liong et al. (1999) p. 16.

The scans are bilevel or JPEG at 150–650 ppi; the table's marks are about 30
pixels tall. Slants and proportions below are measured on the table and
agree with Hirasawa's print.

ト's stem is 804 units long in Regular and 835 in Bold; lengths below are
Regular / Bold.

| Character | Sample | Construction |
| --- | --- | --- |
| 𚿰 TONE-2 | `/`, 21° from upright, nine tenths of tone 7 | ト's stem shortened to 724 / 755 units, turned 21° clockwise |
| 𚿱 TONE-3 | `\`, 15°, nearly as long as tone 7 | ト's stem shortened to 774 / 805 units, turned 15° anticlockwise |
| 𚿲 TONE-4 | short stroke falling to the left | ト's stem shortened to 334 / 365 units, turned 50° clockwise |
| 𚿳 TONE-5 | `<`, arms about 58° from the horizontal | く with each arm turned about the bend to 58° and shortened to 400 units |
| 𚿵 TONE-7 | upright, the longest stroke | ト's stem, 804 / 835 units |
| 𚿶 TONE-8 | short stroke falling to the right | ト's stem shortened to 334 / 365 units, turned 45° anticlockwise |
| 𚿷 NASALIZED TONE-1 | stem with a loop at its foot, like b | ト's stem with the ring at its foot on the right |
| 𚿸 NASALIZED TONE-2 | tone 2 running into a loop, like 6 | ト's stem shortened to 544 / 575 units at the tone-2 slant, its foot ending inside the ring |
| 𚿹 NASALIZED TONE-3 | tone 3 running out of a loop, like 9 | ト's stem shortened to 584 / 615 units at the tone-3 slant, its head ending inside the ring |
| 𚿺 NASALIZED TONE-4 | hollow head with a tail to the lower left | a 160 / 191-unit tail of ト's stem ending inside the ring |
| 𚿻 NASALIZED TONE-5 | `<` with a loop closing the bend; Hirasawa's arms about 65° | く with its arms turned to 65° and shortened to 400 units, the ring across its bend on the left |
| 𚿽 NASALIZED TONE-7 | stem with a loop on its right, below the middle | ト's stem with the ring centred 42% up its right side |
| 𚿾 NASALIZED TONE-8 | hollow head with a short tail to the upper left | a 130 / 161-unit tail of ト's stem ending inside the ring |
| U+0305 | a bar about the width of the kana | ー shortened to FRB's 762 units |
| U+0323 | a round dot under the kana | the halfwidth middle dot ･ |

Shortening compresses only a stroke's straight middle, so its width and flat
terminals stay as Noto draws them. The ring is the handakuten's, widened to
the samples' loop (outer diameter 260 units) by moving both circles outward
the same distance, which keeps the handakuten's ring weight: 45 units in
Regular and 60 in Bold. Contours overlap without being merged, as in Noto
Sans JP's kana, and carry the same overlap flag.

Every join is placed by measuring the outlines. In the samples the stroke
runs into the loop with no terminal showing, so where a stroke ends at the
ring (the 6, the 9 and the hollow heads of tones 4 and 8) its whole flat
terminal lies inside the ring's band, at least 4 units inside both circles:
its nearest point to the centre lies 4 units outside the inner circle and the
ring sits as far to the side as the terminal's corners allow inside the outer
circle. A tail that ends on the ring's own axis is compressed into the band
with its terminal. Beside a stem that keeps its terminals (b, þ) and across
the bend of く, the ring moves as close as the outline lets it while its
counter stays 2 units clear of the stroke. No counter holds any stroke ink.

The checks (`scripts/check_sans_minnan.py`, also run by the font checks)
rebuild each form from the base instance and compare it with the font,
reject contours under 15 units thick or 400 square units in area, and test
the structure on the outlines against a table written from the samples:
the slant of each stroke, the side of the stroke's line and the place along
it where the ring sits, that the joining terminal lies inside the ring's
band, and that the counter holds no ink. They measure every stroke against
the Noto stroke it comes from: ト's stem 83.3 units (Regular) and 137.0
(Bold), く's arms 78.3/86.5 and 129.8/142.6, the ring 44.6 and 59.9, ー 88 and
146, ･ 167 and 195. Each measurement must agree within two units. The median
vertical stem of Noto Sans JP's katakana is 83.0 units in Regular and 136.1
in Bold. In vertical text the existing placement applies: the tone letters sit
beside one to four kana and the marks keep FRB's clearance from the kana.

## Bold drawings

GenZui's own outlines in Bold, measured by the weight gain over Regular
against Noto Sans JP's kana (1.47–1.62, median 1.53):

- **Minnan tone letters:** drawn from Noto Sans JP Bold's own ト, く, ゜, ー
  and ･ on the Regular construction, so each Bold outline has the Regular
  outline's commands and points. Their gains (1.39–1.55) fall within those of
  Noto's kana letters and voicing marks (1.34–1.62); the forms that are mostly
  ring gain least, as the handakuten does (1.34). The dot below gains 1.16,
  within the range of Noto's two middle dots (1.16–1.20), which gain less
  than any kana.
- **Transcription symbols:** the marks inside Noto's dashed frames share one
  stroke per face, the half-turn arrow's ring weight: 36 units in Regular and
  43 in Bold (the frames have 31 and 37). The minus and the double arrow are
  drawn at that stroke; Noto's arrow scaled into the frame would keep a stroke
  of 50 in Regular and 73 in Bold. The Bold half-turn arrow keeps its outer
  edge while its ring and barbs gain 6–7 units inward (`scripts/sans_forms.py`).
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
Minnan tone placement and the drawn Minnan forms, check the refits, and
compare TTF with WOFF2. The coverage audit requires all 763 characters in
Unicode 18's Hiragana/Katakana scripts and script extensions. The browser check
validates the offline specimen in Chromium and Firefox, compares TTF and WOFF2
rasters for both faces and records their hashes; the packager rejects stale
hashes and writes `dist/GenZuiSans-0.103.zip`.

## GenZui Sans P

GenZui Sans P / 源萃ゴシックP applies the font's own `palt` adjustments by
default, for applications such as Word and PowerPoint that ignore the feature.
`scripts/sans_p.py` reads the lookups that `palt` reaches under the DFLT, kana,
hani and latn scripts and their JAN language systems. Every one of them reaches
the same lookups: lookup 6 in Regular, and lookups 6 and 10 in Bold, all
single adjustments in format 2 (11 subtables in Regular, 30 in Bold). They adjust
328 glyphs in Regular and 332 in Bold, with XPlacement and XAdvance values only.

Each glyph's outline moves by its XPlacement, its advance takes the XAdvance
and its left side bearing follows the outline. GPOS mark anchors on moved glyphs
move with them. The `palt` and `halt` features are removed, with the lookups
only they used, so that widths are not applied twice. Other glyphs, cmap, GSUB
and metrics are identical to GenZui Sans.

HarfBuzz centres a vertical glyph on half its horizontal advance. A glyph that
vertical text does not replace through GSUB `vert` would move, so a GPOS `vert`
lookup adds the difference to its XPlacement. Vertical ink is identical to
GenZui Sans; 49 Regular and 58 Bold glyphs depend on this.

`kern` holds 845 kana pair adjustments (format 1, values from -100 to 50), of
which 806 in Regular and 818 in Bold pair two `palt` glyphs, and a Latin class
table that touches none. GenZui Sans applies them to fixed-width kana too, so
they do not assume `palt` widths and P keeps them unchanged. Whether Noto Sans
JP's designers intended them for proportional kana is uncertain.

`scripts/check_sans_p.py` compares P shaped with default features against Sans
shaped with `palt` on, in glyph advances and ink boxes, for every affected
character alone and between kana, each kern pair, marks and running text under
several script and language tags. Vertical text is compared against Sans
vertical, and every other glyph, the cmap and GSUB must be identical. It writes
`build/sans/checks-p.json`. `scripts/package_sans_p.py` writes
`dist/GenZuiSansP-0.103.zip`, a separate download.

```sh
.venv-sans/bin/python scripts/sans_p.py
.venv-sans/bin/python scripts/check_sans_p.py
.venv-sans/bin/python scripts/package_sans_p.py
```

## Site

`scripts/sans_site.py` renders `templates/sans.html` for the development
specimen (`build/site/sans.html`, embedded fonts) and the public site
(`/sans`, fonts from `/sans-v0.103/`). The public build also publishes the
downloads, `/genzui-sans.css`, the social card and the announcement texts.
Version reports live in `research/sans-browser-checks-0.103.json` and
`research/sans-kana-coverage-0.103.json`.

## Provenance check

GenSeki Hentaigana Gothic's README credits Sukima Gothic for most of its
hentaigana and Shokaki Hentaigana Gothic for the rest. Noto Sans Hentaigana
names no source font. `scripts/check_provenance.py` compares drawings: each
glyph is rendered at 160 px on a baseline, cropped to its ink, resized to
96 x 96, blurred (Gaussian radius 4) and compared by Pearson correlation, so
that weight and placement count less than structure. GenSeki's README origin
table (A Shokaki, B Sukima) selects the glyph sets.

```
scripts/check_provenance.py NotoSansHentaigana-Regular.ttf GenSekiHentaiganaGothic.ttf \
    "SukimaGothic-Regular ver11.41.ttf" GenSekiHentaiganaGothic/README.md
```

| Pair | Characters | Median | Above 0.95 |
| --- | --- | --- | --- |
| GenSeki glyphs its README credits to Sukima (B) ↔ Sukima Gothic Main | 205 | 0.999 | 205 |
| GenSeki glyphs its README credits to Shokaki (A) ↔ Sukima Gothic Main | 75 | 0.596 | 0 |
| Noto Sans Hentaigana Regular ↔ Sukima Gothic Main, U+1B002–1B0FF | 254 | 0.624 | 0 |
| Noto Sans Hentaigana Regular ↔ GenSeki glyphs credited to Shokaki (A) | 75 | 0.630 | 0 |

Derived drawings score 0.999; unrelated ones about 0.60. Noto Sans
Hentaigana scores like unrelated drawings against Sukima Gothic and against
GenSeki's Shokaki-derived glyphs. This does not prove independence: it shows
no copying of those outlines. Simple shapes such as small katakana score high
in any sans, so the test says little about them.

Measured on 2026-10-05 with:

- Noto Sans Hentaigana Regular instance compiled from
  https://github.com/notofonts/hentaigana at commit
  `3aa4d30ee04254d3d0a69c500de7fda494e3b302`
- GenSeki Hentaigana Gothic 1.201 Regular and its README,
  https://github.com/MihailJP/GenSekiHentaiganaGothic/releases/tag/v1.201
- Sukima Gothic ver11.41 Main, `SukimaGothic-Regular ver11.41.ttf`, from
  https://booth.pm/ja/items/2117070 (a signed-in BOOTH download)
