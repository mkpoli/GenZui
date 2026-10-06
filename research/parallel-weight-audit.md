GenZui Sans 0.104 and Serif 0.118 are compared at identical em sizes and with the same stroke-measurement method. The paired set contains 375 forms, including all 35 Okinawan forms. Each family has 2,268 raster records across two weights and two resolutions. The vector reference censuses cover 16,732 encoded Noto Sans JP characters and 16,726 encoded Noto Serif JP characters. Serif-only repertoire is outside this comparison.

Serif has intentional thick–thin contrast. Each glyph's median, 75th-percentile and 90th-percentile stroke diameters are therefore compared against the same percentile in its own family's full-size reference kana. The references are identical characters across families. They describe structural comparisons and can differ from the actual construction donors.

For the 27 Funatsu forms, the spread of these reference-normalized widths is:

| Weight | Stroke measure | Sans spread | Serif spread |
| --- | --- | ---: | ---: |
| Regular | Median | 5.7% | 8.3% |
| Regular | 75th percentile | 8.4% | 7.7% |
| Regular | 90th percentile | 7.6% | 9.0% |
| Bold | Median | 9.9% | 12.7% |
| Bold | 75th percentile | 12.1% | 15.8% |
| Bold | 90th percentile | 10.1% | 7.0% |

Spread is the interquartile range divided by the median, expressed as a percentage. Lower values describe more uniform normalized widths. The measurements give mixed evidence for Serif being better balanced: its Bold heavy-stroke measure is more uniform, while its median and 75th-percentile widths are less uniform. This statistic does not measure visual quality. Differences in stroke contrast, component size, spacing and flow can make Serif look more coherent without producing uniform stroke ratios.

The selectable percentiles prevent one stroke measure from determining the result. The 75th percentile is the initial view; all three spreads appear together. Ratios below 100% mean thinner than the full-size comparison kana under that measure. They do not prescribe increasing a compact component to full-size native weight.

Useful individual comparisons at the 75th percentile include:

| Form / weight | Sans / native reference | Serif / native reference |
| --- | ---: | ---: |
| KWE Regular | 105.1% | 88.4% |
| SI Regular | 111.6% | 92.8% |
| Glottal WA Bold | 82.7% | 98.5% |
| HWE Bold | 94.4% | 79.3% |

Serif can be a useful visual reference for proportions and stroke transitions. Its numerical stroke widths cannot be transferred directly to Sans. The HWE comparison illustrates the limitation: the approved Serif form has substantially thinner normalized strokes under this measure.

Both audits use the same [medial-axis distance method](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.medial_axis), axis-length weighting, endpoint/junction exclusions, renderer, environment and 512/1,024-pixel em resolutions. For the Funatsu forms, median absolute resolution changes are 0.2–0.6% across the reported weights and percentiles. Individual glyphs may be less stable; the report flags changes above 5%. The skeleton is sensitive to terminals and branching, especially in Serif. The previous Sans report's remaining measurement limitations still apply.

The maximum raster/vector ink-area discrepancy at 1,024 pixels per em is 0.001082 em² for Sans and 0.001504 em² for Serif. Checks verify font hashes against the immutable release files, matching form coverage, unique raster records, absence of clipping or inserted dotted circles within that area tolerance, and the displayed normalization arithmetic. Connected Serif ふ forms are not subjected to the detached-component separation used in Sans.

The comparison page shows Sans and Serif in parallel columns for every form. Each column includes native comparison letters, the constructed glyph, reading-size context, width percentiles, vector ink coverage, Bold-to-Regular ratios and resolution sensitivity. Full-face webfonts cover the historical-character comparison table. Both family and weight selections are checked against the fonts Chrome actually renders; the two-column mobile layout is also checked.

Reproduce after generating the Sans audit:

```sh
python scripts/serif_parallel_weight_audit.py
python scripts/parallel_weight_report.py
python scripts/check_parallel_weight_audit.py
show build/sans-weight-audit --name genzui-sans-weight-audit
python scripts/check_sans_weight_browser.py
```

The Serif audit took about three CPU minutes with one worker under a 3 GB memory cap and disabled swap. It leaves the published fonts unchanged. `research/parallel-weight-audit.json` contains the findings and source hashes; detailed raw rows remain in the generated report folder.
