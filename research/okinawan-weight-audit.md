The weight audit compares Noto Serif JP at 400 and 700 with GenZui’s 27 Funatsu forms. Every encoded native character receives vector measurements: 16,726 code points, representing 16,087 distinct encoded glyphs, per weight. Unencoded alternates are outside this census. Native kana and constructed forms also receive raster stroke measurements at 512 and 1,024 pixels per em.

`okinawan-weight-audit.json` records the source hashes, library versions, script distributions, individual comparisons and sampling sensitivity. `okinawan-weight-browser-checks.json` records the local report’s desktop/mobile controls and the design proof’s revised/confirmed state. Full native rows are generated as `build/okinawan-weight-audit/native-all.csv`; the interactive report searches every row.

Area is the filled union area. Effective width is twice that area divided by Bézier perimeter. Stroke diameters come from a Euclidean distance transform sampled on the medial axis and weighted by local axis length. Junction and terminal neighbourhoods are excluded; this can exclude nearby thin strokes too. Direction bins need at least 60 units of supported axis and agreement within 10% between resolutions. These measurements describe geometry, not a perceptual equivalence model. Script ranges deduplicate aliases and omit empty outlines; they are descriptive distributions rather than uniform design targets.

The before snapshot uses the drawings at `f2b2f85`. Preserve those built fonts before rebuilding the revised source. Snapshot reuse is explicit: a phase name whose saved font differs from the current build fails unless `--reuse-snapshot` is supplied. To reproduce the audit, run the following from the repository with its Python environment, taking the before measurements before the revised font build:

```sh
python scripts/okinawan_weight_audit.py --native --phase before --pixels 512
python scripts/okinawan_weight_audit.py --strokes-only --phase before --pixels 1024
# Rebuild the revised Regular and Bold fonts with serif.py and bold.py.
python scripts/okinawan_weight_audit.py --phase after --pixels 512
python scripts/okinawan_weight_audit.py --phase after --pixels 1024
python scripts/okinawan_weight_report.py
```

The Regular correction changes 11 unvoiced bodies and six voiced counterparts. Bold, WU, SI/ZI, YU, WA/WI/WE, N, YI and YE retain their prior outlines. TI’s added upper-arm thickness is bounded at 2.5 units; its elbow, cap and right stroke remain exact. Earlier confirmed fingerprints remain in `confirmed-bodies.json`; the new weights are recorded separately in `weight-revision-bodies.json` for review.
