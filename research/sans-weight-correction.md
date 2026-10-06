GenZui Sans 0.105 corrects the weight differences measured in the 0.104 audit. The 27 Funatsu forms have lower spread under each of the three reported stroke measures, in both weights. Hentaigana’s thicker-stroke level is close to the family-relative level measured in Serif.

| Native-relative width spread | Regular 0.104 | Regular 0.105 | Bold 0.104 | Bold 0.105 |
| --- | ---: | ---: | ---: | ---: |
| Median stroke | 5.7% | 4.5% | 9.9% | 7.3% |
| 75th-percentile stroke | 8.4% | 6.8% | 12.1% | 9.3% |
| 90th-percentile stroke | 7.6% | 6.9% | 10.1% | 6.5% |

Spread is the interquartile range divided by the median of each form’s reference-normalized width. These figures describe geometry. They do not establish perceptual equality with Serif. The [parallel audit](parallel-weight-audit.md) explains the normalization, numerical sensitivity and limits.

Regular KWE/GWE use 79.04-unit connecting strokes instead of 85.12. Regular SI/ZI use Noto weight 450 for the す body and small-ぃ mark, replacing weight 500. Their accepted skeletons and native stroke shapes remain the basis of the drawings.

HWA’s compact わ gains four units of outline weight in Regular and eight in Bold. The Bold vowel moves six units right to retain separation from ふ. HWE’s vowel strokes increase from 66/98 to 70/106 units. HWI retains its existing outlines. Bold glottal WA/WI/WE use the weight-900 native donor for the reduced body and top mark; WE’s separately fitted top mark uses weight 850. Their mark lengths, slopes and placement follow the same fitting rules.

All 286 hentaigana use the pinned Noto Sans Hentaigana source at axes 410/770, replacing 380/720. Their median native-relative 75th-percentile widths move from 94.6%/92.7% to 100.8%/97.6%. The corresponding Serif values are 100.9%/97.7%. Source instance interpolation supplies the shapes; no uniform outline expansion is applied to hentaigana. Some tiny gaps close as the native strokes grow. Visual review of the affected joins found no clear reading defect, and independent checks found no new dakuten or handakuten collisions.

The full family still contains 17,096 encoded characters. The sentence-ready Okinawan subset still contains 805. Existing advance widths, mappings and shaping placements remain unchanged. Exact glyph comparisons against 0.104 restrict Okinawan changes to six Regular forms and five Bold forms, plus the 286 hentaigana in each weight. Other glyphs and metrics must remain exact. Published Serif assets and prior release directories are unchanged.

Donor compilation uses `requirements-sans.lock` in `.venv-sans`, the source archive pinned in `sources/sans-manifest.json`, and a fixed source epoch. The build checks the pinned source hash, instance axes and compiled donor hashes. The full package records these inputs in `hentaigana-weight-sources.json`; its NOTICE and per-character source descriptions identify the new axes. Direct glyph import preserves the donor outlines exactly.

The build and structural checks are documented in the [release procedure](sans-okinawan.md#release). To reproduce the numerical correction proof after generating the baseline Sans and Serif audits:

```sh
python scripts/measure_sans_revision.py
python scripts/check_sans_weight_correction.py
python scripts/parallel_weight_report.py
python scripts/check_sans_weight_browser.py
```

`sans-weight-correction.json` binds the measurements to the final full-font SHA-256 hashes. The report compares 0.105 with 0.104 and Serif 0.118. It includes both weights, native references, every Okinawan form, reading samples and all 375 matched forms. Browser checks verify the actual full-font faces and compare rendered KWE ink between the two Sans releases.
