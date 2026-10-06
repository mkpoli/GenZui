# GenZui Sans Okinawan

GenZui Sans Okinawan supplies the same 27 Funatsu forms and eight raised
katakana as the Serif family, in Regular and Bold. Each sentence-ready face
contains 805 encoded characters: kana, punctuation, Latin, combining marks
and the special forms. The extended full Sans faces contain 17,096 encoded
characters.

## Drawings

The drawings use Noto Sans JP's native Regular and Bold masters at weights
400 and 700. Reduced components use weights 450–900 for optical
compensation. The ふ head and body retain their native dimensions and weight.
TU and WU use continuous strokes through their lower turns, and glottal
WA/WI/WE use the native こ upper-mark contour. WE fits its mark to the
longer ゑ head using the accepted WI mark-to-head relationship. New joining strokes follow cubic skeletons with flat Sans
terminals. Their widths are set separately for each weight. The drawings
reuse no Serif outlines and apply no blanket outline expansion.

`okinawan_sans.py` supplies the drawings and their dakuten placement.
`okinawan.py` shares the mapping, glyph registration, metrics and composition
lookup with Serif. Voiced Funatsu forms use a private-use base followed by
U+3099; YI and YE use ordinary い and え followed by U+3099. Raised katakana
have a half-em advance. See [the mapping registry](../data/okinawan/mappings.json)
for character identities and reference sources.

## Build and proof

Use the ordinary project environment and pinned sources described in the
[README](../README.md):

```sh
.venv/bin/python scripts/sans_okinawan.py
.venv/bin/python scripts/check_sans_okinawan.py
.venv/bin/python scripts/sans_okinawan.py --package
show build/sans-okinawan
```

For the Windows Chrome check, keep the proof registered with `show` and run
`.venv/bin/python scripts/check_sans_okinawan_browser.py`. It uses the existing
GenZui browser registry and verifies the rendered font at every comparison
and sentence, plus the two-column layout at a 390-pixel viewport. It checks
the collapsed groups, Serif references and optical-reference font families and captures the raised-katakana
comparison at a 2× device pixel ratio.

The output directory contains the subset TTF/WOFF2 files, CSS and an editable
proof. The proof shows all 35 forms in two columns, with native kana beside
each drawing, small-size comparisons and dictionary sentence samples. Each
card includes a compact comparison in the matching weight of GenZui Serif
Okinawan 0.118. Those immutable reference webfonts and their notices are
included in the proof package, with hashes checked against the release.
HWI, HWE, YO and WE also show related native and Okinawan forms alongside each
drawing, with a compact Serif row for the same characters. When
`previous/Regular.woff2` and `previous/Bold.woff2` are present, each card also
includes an expandable comparison with that earlier drawing. The package
includes these comparison fonts when available.

HWA/HWI/HWE use separate left dots and right vowel components. HWE uses
a softened え corner with a diagonal and a baseline foot, drawn separately
for Regular and Bold at stroke widths of 70/106 units. The 0.105 calibration adds weight to
the compact vowel while retaining its accepted shape. The Bold foot branch
is trimmed to the diagonal's left edge to remove an exposed starting cap.
The family comparison shows all three beside native ふ in both weights.

YU’s glottal mark uses lighter 450/700 donors while retaining its height,
slope and alignment with ゆ’s left stroke. YO uses 475/900 donors at heights
of 480/500 units. Both approved YO drawings are unchanged. WE's upper mark uses 475/850 optical donors. Its length, slope,
left offset and visible midpoint gap follow WI's relationship to its head
bar, fitted to ゑ's longer head. Its reduced body retains 500/900 donors.
TU uses the native 700 donor for its Bold upper stroke. WU Regular uses a
450 donor for the upper body and
a 70-unit return, while Bold retains its 116-unit return. Its upright extends
farther below the crossing. A local correction restores weight lost from
the upper arch during vertical compression, preserving the native tangents.
Bold’s top bar is raised slightly to retain space above the arch. Confirmed
forms (24, including HWI) are collapsed by default. The nine corrected forms
are at the top, with both weights and expandable previous drawings. Raised Sans
Regular katakana use the approved 450 donor; Bold retains 700. Serif references
use the selected 500/750 raised forms, generated separately from the immutable
0.118 release. Published Serif files are unchanged.

HWA uses the selected native わ curve with its crossbar removed. The cut
closes inside the upright. Its 800/900 donors retain the selected 43%/40%
horizontal scaling and 43% height. Outline strokes of 12/40 units restore
weight in the reduced vowel. Its placement retains at least 30 units of
whitespace from ふ.
The native ふ outlines are unchanged. HWI uses 72/110-unit vowel strokes,
a roughly 5% reduction from 76/116, preserving the accepted skeleton and
component placement. HWI is unchanged in 0.105.

`measure_sans_fu.py` reports `2 × filled area / contour perimeter` for the
compiled vowel contours and native reference kana. This approximates ink
breadth; proportions, junctions and terminals also affect the result, so it
is a comparison aid rather than a perceptual target. The HWI proof includes
the before/after table alongside the full family and native わ/い/え.
The [earlier measurement report](sans-fu-weight-measurements.json) records the
HWI adjustment included in 0.104. The [0.105 correction report](sans-weight-correction.md)
uses local stroke measurements for the current HWA/HWE changes and the other
recalibrated forms.

`full/` contains the extended full-family faces. The subset ZIP is written to
`dist/GenZuiSansOkinawan-0.105.zip` after validation.

This build extends the immutable Sans 0.103 fonts. It checks their hashes
against the release's validation records and verifies the Noto source files
against the pinned manifest. It preserves the published Sans repertoire
while adding the 26 encoded private-use bases; voiced forms are composition
glyphs. Unreleased gugyeol changes in the general Sans source builder are
outside this extension. The versioned 0.103 assets remain immutable.

## Verification

The checker compares every unchanged glyph’s compiled outline and horizontal
and vertical metrics with Sans 0.103 and 0.104. The 286 reweighted hentaigana
match their pinned-source donors exactly; their advances and shaping placements
remain unchanged. An explicit per-weight whitelist covers the corrected Okinawan forms. Every previously encoded character is
also shaped in both directions. It checks the subset repertoire, family
metadata, all 35 forms, native combining sequences and sentence samples,
including TTF/WOFF2 parity. It verifies exact non-intersection of dakuten and
their bases, an additional sampled clearance margin, and separation of the
TSI and HWA strokes that should remain distinct. Detached glottal marks and
vowel strokes have additional minimum-clearance checks in both weights.
The ふ forms are checked for dot/body separation and cell bounds. HWE Bold
also checks that its outer diagonal stays straight through the foot join.
Raised katakana are checked against each donor’s transformed
bounds, including its native baseline overshoot.

These checks establish structural correctness and preservation of existing
characters. Visual review of the joins, counters and balance remains part of
approving new font drawings.

## Character proof

![Regular and Bold beside native kana](sans-okinawan-proof.png)

## Release

Version 0.105 calibrates selected Okinawan strokes and uses hentaigana donor
axes 410/770. The donor compiler runs automatically before the font build;
install `requirements-sans.lock` in `.venv-sans` first.
The [weight correction report](sans-weight-correction.md) records the changes.

The public full-family files are staged separately in `build/sans-release/`.
The public subset is in `build/sans-okinawan-release/`; both specimens show
all 35 forms and editable sentences. Design alternatives and previous drawings
stay in the development proof. Source notices and baseline validation records
accompany the full package.

```sh
.venv/bin/python scripts/sans_okinawan.py
.venv/bin/python scripts/check_sans_okinawan.py
.venv/bin/python scripts/sans_okinawan_release.py
show build/sans-release --name genzui-sans-release
show build/sans-okinawan-release --name genzui-sans-okinawan-release
.venv/bin/python scripts/check_sans_okinawan_release_browser.py
.venv/bin/python scripts/sans_okinawan_release.py --package
.venv/bin/python scripts/check_sans_okinawan_release.py
.venv/bin/python scripts/sans_okinawan_sns.py
bun run release:build
.venv/bin/python scripts/check_release.py
```

The staging step verifies the reviewed full TTF/WOFF2 hashes, copies the
subset, and records every staged asset. Packaging checks those hashes and
rejects unexpected files. The browser check renders all forms in both full
and subset fonts at desktop and mobile widths. ZIP names are
`GenZuiSans-0.105.zip` and `GenZuiSansOkinawan-0.105.zip`.

The SNS cards are 2400×1260 PNGs with Regular and Bold in two columns.
The Funatsu card includes all 27 forms and two dictionary sentences;
the follow-up includes all eight raised signs with notation examples.
Japanese posts, an English Funatsu post, alt text and source records accompany
the images in `build/sans-okinawan-social/`.

The production branch is `main`. Release assets and site deployment must be
built from its clean merged commit. The immutable `sans-v0.105` directory
contains the full and subset TTF/WOFF2 files, both CSS files and both ZIPs.
