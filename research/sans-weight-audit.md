GenZui Sans 0.104 has measurable differences in stroke thickness, particularly in its Bold Okinawan forms. Native Noto Sans JP supplies the reference at weights 400 and 700. Published font files remain unchanged.

The census measures all 16,732 encoded native characters in both weights. Detailed stroke measurements cover 375 GenZui comparison forms and 192 native references at 512 and 1,024 pixels per em: 2,268 raster records. The comparison set includes 27 Funatsu forms, eight raised katakana, historical kana and specialist symbols. Some historical targets already have native mappings; this is not a count of newly encoded characters. Unencoded alternates outside the explicit Okinawan sequences are excluded.

| Group | Regular median | Bold median | Regular middle 80% | Bold middle 80% |
| --- | ---: | ---: | ---: | ---: |
| Native full-size hiragana, 48 letters | 74.2 | 120.1 | 70.3–80.6 | 113.3–131.1 |
| Native full-size katakana, 48 letters | 81.4 | 130.9 | 76.2–84.2 | 121.7–138.6 |
| Funatsu, 27 forms | 75.8 | 115.6 | 68.7–82.4 | 100.4–127.9 |
| Hentaigana, 286 forms | 69.1 | 106.6 | 64.7–73.4 | 99.2–116.4 |

Values are font units on a 1,000-unit em. Each glyph contributes its axis-length-weighted median stroke diameter; group statistics then weight glyphs equally. The ranges describe natural geometric variation. They are not acceptance bands or universal weight targets.

The strongest candidates for a correction proof are:

- **Regular KWE/GWE and SI/ZI:** KWE and SI measure 84.5 and 84.0 units. Their medians exceed the medians of their full-size comparison letters by about 10%. GWE and ZI show the same tendency. Compare thinner versions while preserving the approved shapes.
- **Bold glottal WA/WI/WE:** medians of 103.5, 101.3 and 93.9 units, respectively, are roughly 15%, 17% and 20% below their full-size comparison summaries. Their Bold-to-Regular ratios are only 1.38–1.41, compared with roughly 1.62 for the native hiragana group medians. Review the components and their distribution of thickness before selecting an increase.
- **HWA and HWE vowel components:** their medians are about 8–11% thinner than the retained ふ parts, in both weights. These regions differ in structure: the retained ふ omits its native right stroke and includes a reduced left dot. The difference supports examining the vowels; it does not establish that every stroke should have equal thickness.
- **Hentaigana:** group median widths are about 7% lower in Regular and 11% lower in Bold than the native hiragana reference. A denser, more complicated glyph can need thinner strokes. Compare the donor weight axis at reading sizes before changing the group.

HWI's vowel and retained ふ medians differ by only 0.3% in Regular and 1.8% in Bold. It is a lower priority for weight adjustment. TU, TI, KWA and KWI have Regular medians near 75–76 units and Bold medians near 116 units. These whole-glyph measurements do not suggest thinning all constructed kana together.

The measurements support a component-level correction proof. They do not determine exact outline offsets: joins, counters, dots, component size and spacing affect perceived weight. Raised katakana, small kana, tone marks and ideographic-description symbols need their own size conventions and references.

The `donors` fields name full-size comparison kana, not an inventory of construction donors. SI and glottal N contain small ぃ strokes but compare against full-size い. Glottal WA includes わ as a structural comparison; its drawing derives from ゐ and こ.

Local stroke diameter is twice the Euclidean distance from the medial axis to the nearest ink boundary. Samples near endpoints and junctions are excluded, then weighted by local axis length. The implementation uses [scikit-image's medial axis transform](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.medial_axis). Residual terminal branches and excluded narrow regions can bias individual quantiles. Direction estimates require at least 60 units of supported axis and agreement within 10% between resolutions; raw values and stability flags remain available.

The median absolute change from 512 to 1,024 pixels per em is 0.42% in Regular and 0.38% in Bold. The 95th percentiles are 2.50% and 2.27%. Bold HWE’s retained ふ median changes by 4.6%, which limits fine component comparisons. Some small marks have changes exceeding 16%, so their fine differences should not be interpreted. Synthetic straight strokes and rings have a maximum median-width error of 3.29 units across both resolutions. These checks establish numerical sensitivity, not perceptual accuracy. The isolated underdot has insufficient stable axis support; its stroke width is reported as unavailable.

The auxiliary vector metric is twice filled union area divided by Bézier perimeter. It varies with stroke length, ends and joins. Matching group medians of this metric can conceal differences in actual stroke diameter. Native script summaries deduplicate encoded glyph aliases. The 48-letter native kana cohorts contain no aliases.

The raster/vector ink-area comparison catches clipping, unexpected glyphs and dotted-circle insertion on standalone marks. Its maximum discrepancy at 1,024 pixels per em is 0.001082 em². Standalone combining marks use BASIC rendering; composed Okinawan sequences use HarfBuzz through RAQM. HWA/HWI/HWE vowel measurements select complete detached components wholly to the right of x=500, without cutting through strokes.

To reproduce with the repository's Python environment and pinned upstream fonts:

```sh
python scripts/sans_weight_audit.py
python scripts/sans_weight_report.py
python scripts/check_sans_weight_audit.py
show build/sans-weight-audit --name genzui-sans-weight-audit
python scripts/check_sans_weight_browser.py
```

The audit takes about three CPU minutes with one worker. Its medial-axis and vector geometry implementations run on CPU. The reference run used a 3 GB memory cap with swap disabled. The browser check requires the repository's Windows Chrome configuration. It verifies the Regular/Bold control, search, complete form count, actual specimen font and mobile layout.

`research/sans-weight-audit.json` records the numerical findings and source hashes. The generated report includes native-source comparisons, reading-size samples, small Serif references, a searchable table of all 375 forms, the full vector census, detailed measurements and environment versions.
