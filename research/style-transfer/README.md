# Paired Serif → Sans pilot

The target appearance is Noto Sans CJK. This experiment learns from paired
Noto Serif CJK / Noto Sans CJK drawings, then applies the conversion to Noto
Serif Tangut. It produces experimental raster fields and traced SVGs.
The 0.002 font remains the geometric baseline; neither method is ready for use
as GenZui Sans Tangut.

## Results

Mean results on **256 withheld CJK characters**, at a shared origin, baseline
and 224 pixels per em:

| Method | Ink overlap (IoU) ↑ | Boundary error ↓ | Ink / target | Component and hole counts agree |
| --- | ---: | ---: | ---: | ---: |
| Unchanged Noto Serif | 56.55% | 13.79 | 0.779 | 49.2% |
| Geometric heuristic 0.002 | 60.04% | 14.60 | 0.897 | 46.5% |
| Learned, shared-feature constraint | 71.40% | 10.61 | 1.038 | 32.8% |
| Learned, without constraint | 71.27% | 10.53 | 1.015 | 37.9% |

Boundary error is the symmetric mean distance between binary ink boundaries,
in a 1,000-unit em. There is no additional alignment during scoring. Empty
predictions are counted separately and excluded from boundary-distance
averages; these runs have none. The full records include medians, 95th
percentiles and extra/missing component and hole counts.

The learned models approach the CJK target's ink distribution, but round
corners, merge gaps and sometimes split a thin stroke. The unconstrained run
splits the simple 丨 control. Counting components and holes is a raster
diagnostic: a count match cannot establish character correctness, and intended
Serif/Sans design differences can change the counts.

The regularizer's 0.13 percentage-point overlap advantage comes with worse
boundary error and topology counts. These single-seed runs do not demonstrate
separation of content and style. The 140 Tangut samples have **no Sans ground
truth**; CJK scores cannot establish Tangut quality.

## Experiment

The fixed [split](split.json) has 2,048 training characters, 256 validation
characters, 256 test characters and 80 stress forms. Code points are disjoint;
recurring components are allowed. Byte-identical pairs are rejected. The
stress aggregate excludes 一 and 丨 because the heuristic directly uses their
Noto Sans outlines. They remain separate donor controls. Tangut never enters
training or checkpoint selection.

The network has 388,241 parameters: four spatial encoder levels, skip
connections, a decoder conditioned on a Serif/Sans code, and a signed-distance
output. The conditioning follows the affine feature modulation described by
[Perez et al., FiLM (2017)](https://arxiv.org/abs/1709.07871); the spatial
encoder/decoder follows the general approach of
[Ronneberger, Fischer and Brox, U-Net (2015)](https://arxiv.org/abs/1505.04597).
This is a smaller, independent implementation; no pretrained weights are used.

Both runs use 2,400 AdamW steps, batches of 12, learning rate 0.001, seed
20261027, BF16 CUDA computation, 80% cross-style examples and 20% identity
examples. The loss combines signed-distance, Dice and binary cross-entropy
terms. One run adds 0.02 times the paired bottleneck-feature L1 distance; the
ablation uses zero. Validation IoU selects each checkpoint. Skip connections
can retain source style, and the bottleneck is not an explicit stroke graph.

The heuristic keeps the existing Tangut width rule and geometric operations.
A winding adapter lets its contour grouper read CFF CJK outlines. It has no
CJK stem-zone hints; it still reads the pinned Tangut archive. It works from
vector outlines and a 640-pixel/em intermediate raster, while the learned
model sees 224-pixel/em input. This is a test of the existing conversion on
CJK, with its original calibration, rather than a CJK-tuned baseline.

The proof shows original vector paths for the fonts and zero contours of the
learned 256 × 256 fields. Tracing gives crisp display edges but does not fit
Bézier curves, enforce square terminals, recover strokes or add hinting.
Browser checks compare 48 traced outlines with their threshold masks.
They also compare 72 native font outlines with FreeType rasters. Those font
rasters can be grid-fitted; all differences in the recorded run fit within
one pixel at 224 pixels per em.

The Tangut structure screen measures surviving substantial source ink regions
and counters, plus changes in component/hole counts. Its 10% retained-area
threshold catches nearly lost regions. It cannot judge small joins, stroke
grammar or the intended Sans design.

Among 140 Tangut samples, the shared-feature model nearly closes **5 substantial
source counters across 4 glyphs** and the unconstrained model closes **6 across
5 glyphs**; the heuristic closes none under this screen. None loses a
substantial ink region entirely.
Component counts change in 80, 82 and 9 glyphs respectively. Those changes
include small joins and splits and require inspection. The proof can filter
to the counter-closure cases.

## Outline cleanup

| Model | CJK test overlap, raw → fitted | Tangut path segments | Original retained |
| --- | --- | --- | --- |
| Shared-feature constraint | 71.40% → 71.34% | 323,457 → 19,842 | 1/140 |
| Without constraint | 71.27% → 71.21% | 324,854 → 19,898 | 1/140 |

The cleanup view compares the raw learned contour with fitted straight segments
and cubic Bézier curves. It resamples each contour by arc length, smooths the
samples, and fits curves by least squares. Four strengths are tried in descending
order. A fit must stay within 1.1 pixels of the sampled source boundary, keep at
least 94% ink overlap at 512px, and retain one-to-one correspondence of ink regions
and enclosed counters at both 256px and 512px. If every fit fails, the original
contour is retained. These raster checks do not prove continuous topology at
other scales.

The pass preserves the learned terminal and join design. Rounded ends, uneven
stroke weights and already-closed counters remain. The full 952-case report and
source bindings are in `cleanup.json`; `cleanup-checks.json` records integrity
and geometric regression checks. Each source SVG, reference PNG, inference
manifest, fitting script, scoring script and serializer is bound by SHA-256.

Raster controls use an explicit zero-width pen with the fill brush.
[aggdraw's implementation](https://github.com/pytroll/aggdraw/blob/main/aggdraw/_aggdraw.cxx)
expands brush-only contours; the zero-width pen retains the original fill area.
The checker verifies a 20×20 rectangle has 400 pixels of ink, as well as empty fields
and component/counter loss. Browser checks compare 48 fitted SVGs with their
raster controls in Chromium and Firefox.

Related tracing reference: Peter Selinger,
[Potrace: a polygon-based tracing algorithm](https://potrace.sourceforge.net/potrace.pdf)
(2003). This experiment uses its own least-squares curve fitter, without Potrace
code.

## Sources

The [source manifest](../../sources/style-manifest.json) pins URLs, sizes and
SHA-256 hashes for Noto Serif CJK JP Regular, Noto Sans CJK JP Regular, Noto Serif
Tangut, the Tangut Glyphs archive, Lorchin Sans 2.500 and their licenses. The
Noto files use SIL OFL 1.1. Lorchin's repository provides WTFPL; exact upstream
Tangut glyph revisions remain unverified. Lorchin is a visual comparison only.
The geometric font's sources are described in [the font report](../tangut-sans.md).

Related work: [Park et al., MX-Font (ICCV 2021)](https://github.com/clovaai/mxfont)
learns localized style features with component supervision and reports Chinese
to Korean transfer. That offers a stronger component-based direction for a
future Tangut experiment. This pilot uses neither its code nor its checkpoint.

## Reproduce

Python 3.14, PyTorch 2.11.0+cu128 and an RTX 5070 Ti were used. Each training
run took about two minutes and peaked at 3,904 MiB of allocated VRAM. Raster
generation and geometric reconstruction use CPU libraries. Check available
RAM/VRAM before running; run GPU jobs sequentially.

```sh
uv venv --python 3.14 .venv-style
uv pip install --python .venv-style/bin/python --torch-backend cu128 -r requirements-style.txt
systemd-run --user --unit genzui-style-data --slice=batch.slice -p MemorySwapMax=0 --same-dir -- .venv-style/bin/python scripts/style_data.py
```

Wait for each unit to finish successfully (`journalctl --user -u <unit>`).
Then run these commands in separate units with the same batch wrapper:

```sh
.venv-style/bin/python scripts/style_baseline.py --workers 4
.venv-style/bin/python scripts/style_network.py --name dual-style
.venv-style/bin/python scripts/style_infer.py dual-style
.venv-style/bin/python scripts/style_network.py --name no-latent --regularize 0
.venv-style/bin/python scripts/style_infer.py no-latent
.venv-style/bin/python scripts/style_metrics.py dual-style no-latent
.venv-style/bin/python scripts/check_style_transfer.py
```

For the Tangut comparison, first build the 0.002 font using the
[font instructions](../tangut-sans.md#build-and-inspect), then run
`style_tangut_structure.py`, `style_cleanup.py`, `check_style_cleanup.py`, and
`style_specimen.py` in batch units.
`devrun node scripts/check_style_browser.mjs` checks the proof in Chromium and
Firefox. The existing browser executable environment variables are supported.
The offline proof is `build/style-transfer/proof/index.html`.

Training refuses an existing run directory. Preserve or move a completed run
before reusing its name. Checkpoints and arrays stay under `build/`; the
recorded JSON files beside this report preserve the measurements, split,
training history and checksums. cuDNN benchmark mode can vary results between
runs despite fixed seeds. Reproduction means rerunning the fixed experiment;
bit-identical weights are not promised.

The next useful experiment is a stroke-aware decoder with explicit endpoints,
joins and counter constraints, evaluated against the same CJK target. It
needs a separate test set once these examples guide model design. Scaling this
pilot to the full Tangut repertoire would reproduce its current defects.
