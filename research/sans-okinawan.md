# GenZui Sans Okinawan

GenZui Sans Okinawan supplies the same 27 Funatsu forms and eight raised
katakana as the Serif family, in Regular and Bold. Each sentence-ready face
contains 805 encoded characters: kana, punctuation, Latin, combining marks
and the special forms. The extended full Sans faces contain 17,096 encoded
characters.

## Drawings

The drawings use Noto Sans JP's native Regular and Bold masters at weights
400 and 700. Reduced components use weights 500 and 800 for optical
compensation. New joining strokes follow cubic skeletons with flat Sans
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
and sentence, plus the two-column layout at a 390-pixel viewport.

The output directory contains the subset TTF/WOFF2 files, CSS and an editable
proof. The proof shows all 35 forms in two columns, with native kana beside
each drawing, small-size comparisons and dictionary sentence samples.
`full/` contains the extended full-family faces. The subset ZIP is written to
`dist/GenZuiSansOkinawan-0.104.zip` after validation.

This build extends the immutable Sans 0.103 fonts. It checks their hashes
against the release's validation records and verifies the Noto source files
against the pinned manifest. It preserves the published Sans repertoire
while adding the 26 encoded private-use bases; voiced forms are composition
glyphs. Unreleased gugyeol changes in the general Sans source builder are
outside this extension. The published site and immutable 0.103 files remain
the source for the current release until the new drawings are approved.

## Verification

The checker compares every existing glyph's compiled outline and horizontal
and vertical metrics with Sans 0.103. Every previously encoded character is
also shaped in both directions. It checks the subset repertoire, family
metadata, all 35 forms, native combining sequences and sentence samples,
including TTF/WOFF2 parity. It verifies exact non-intersection of dakuten and
their bases, an additional sampled clearance margin, and separation of the
TSI and HWA strokes that should remain distinct.

These checks establish structural correctness and preservation of existing
characters. Visual review of the joins, counters and balance remains part of
approving new font drawings.

## Character proof

![Regular and Bold beside native kana](sans-okinawan-proof.png)
