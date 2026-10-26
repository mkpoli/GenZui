# GenZui Sans Tangut

**GenZui Sans Tangut Regular / 源萃ゴシック西夏文字**, version 0.001, is a
development companion to GenZui Sans. It uses Noto Serif Tangut's character
structures, with square Gothic terminals and strokes from Noto Sans CJK JP.

The font contains the Tangut repertoire of Noto Serif Tangut 2.168: **6,145
ideographs, 768 components and U+16FE0 TANGUT ITERATION MARK**. Space and NBSP
bring the encoded total to 6,916. Later Tangut additions and Components
Supplement are absent. This is source-font coverage, not complete Unicode 18
Tangut coverage.

## Sources

| Source | Role | Pinned input |
| --- | --- | --- |
| [Noto Serif Tangut](https://github.com/notofonts/tangut), 2.168 | Character structures and repertoire | [Regular TTF](https://github.com/notofonts/noto-fonts/blob/526169d273a5d9b22035d72ec509932fb7abd59a/unhinted/ttf/NotoSerifTangut/NotoSerifTangut-Regular.ttf) |
| [Noto Sans CJK](https://github.com/notofonts/noto-cjk), JP Regular 2.004 | Horizontal 一 and vertical 丨 stroke outlines; missing-glyph box | [Regular OTF](https://github.com/notofonts/noto-cjk/blob/f8d157532fbfaeda587e826d4cd5b21a49186f7c/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf) |

Both source fonts use SIL OFL 1.1. Their unmodified licence texts are kept in
`sources/upstream/` and included in the package. The new family has its own
name and carries both source copyright notices. The
[source manifest](../sources/tangut-manifest.json) pins all four input files,
including licences, by URL, byte size and SHA-256. Generated `sources.json`
adds script hashes, library versions and construction records for every glyph.

The [Noto Tangut project](https://github.com/notofonts/tangut) credits Yang
Xicheng and Liu Zhao for development and design, Eiso Chan for font engineering,
Kushim Jiang for technical work, and Song Peilin as design assistant. Its README
lists the advisers and project history.

## Construction

The builder works in the source fonts' 1,000-unit em square:

1. Separate the serif contours into ink regions, attaching counters by actual
   containment. Rasterize each region at 640 pixels per em.
2. Extract centre lines with scikit-image's
   [skeletonize](https://scikit-image.org/docs/stable/api/skimage.morphology.html#skimage.morphology.skeletonize).
   Prune short terminal branches while checking whether they continue through
   a crossing. Distances use Euclidean arc length.
3. Fit the Sans donor outlines to nearly horizontal and vertical segments.
   Smooth other segments into cubic paths and stroke them with square terminals
   and miter joins through [Skia PathOps](https://github.com/fonttools/skia-pathops).
4. Recover long vertical stems from the original ink when pruning shortened
   them. Check the original stroke direction to avoid placing vertical pegs on
   diagonal terminals. A recovered centreline must follow original ink on at
   least 95% of its rows, so offset uprights cannot bridge a counter.
5. Union the outlines and convert curves to quadratic TrueType contours with
   FontTools. Keep 1,000-unit horizontal and vertical advances for Tangut.

Stroke width is `64 × min(1, √(3600 / L))`, where `L` is the glyph's total
centre-line length in font units. Dense forms receive thinner strokes. Curved
strokes are reconstructed; the source supplies their placement, and the Sans
font supplies the straight stroke shapes.

## Limits

This method preserves character placement but changes contour details. It
needs further proofreading at dense joins, hooks and small counters. Some
very small gaps close; U+188BB is a known example. Automated coverage and
outline checks do not establish that every character is typographically
correct. The repertoire has not been proofread in full.

The face is Regular only, unhinted, with no Latin, kana or general punctuation.
Install it beside GenZui Sans, or add it after GenZui Sans in a CSS font stack.
It does not replace the existing Japanese fonts or enter the public website
release build.

## Build and inspect

The Tangut build is verified with Python 3.14 and the root dependency lock.
Use a separate environment beside the Serif and Sans environments:

```sh
uv venv --python 3.14 .venv-tangut
uv pip sync --python .venv-tangut/bin/python requirements.lock
.venv-tangut/bin/python scripts/tangut_sans.py --workers 4
.venv-tangut/bin/python scripts/check_tangut_sans.py
.venv-tangut/bin/python scripts/tangut_specimen.py
bun install --frozen-lockfile
bunx playwright-core install chromium firefox
devrun node scripts/check_tangut_browser.mjs
.venv-tangut/bin/python scripts/package_tangut_sans.py
```

The builder fetches and verifies missing sources. `--sample` builds 22 design
samples; packaging requires the full build. Output is in `build/tangut-sans/`:
TTF, WOFF2, CSS, an offline comparison specimen and a ZIP with licences and
validation reports. Open `index.html` to compare the source and new face,
browse components, search code points and type sample text. The specimen and
font downloads work without external assets.

The browser check starts a temporary local server and closes it after checking
Chromium and Firefox. `CHROMIUM_EXECUTABLE_PATH` and `FIREFOX_EXECUTABLE_PATH`
can select installed browser binaries. Its screenshots use 2× pixel density,
in light and dark themes. On systems without `devrun`, run the same Node script
inside the local resource-management wrapper.

Font checks cover exact source coverage, nonempty outlines, winding, metrics,
TTF/WOFF2 parity, horizontal and vertical HarfBuzz shaping, counter containment,
crossing continuation and recovered stems. A whole-repertoire screen requires
at least 10% overlap for source ink regions of 1,000 square units or more and
at least 10% retained white area for counters of 2,000 square units or more.
These thresholds catch whole lost regions; they do not rate visual quality.
Browser checks cover font loading,
raster parity at four sizes, specimen controls and mobile layout. Packaging
rejects stale font or specimen reports and verifies every ZIP member.
