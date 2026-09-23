"""Match GenZui drawings to Noto Serif JP Bold's vertical stems.

In the pinned Noto Serif JP variable font, the median vertical stem of ト
is 60 units at Regular (wght 400) and 105 units at Bold (wght 700).
Horizontal strokes, such as 一, stay near 33 units. Bold is a horizontal
dilation of Regular: 22.5 units on each side. Noto's own Bold outlines
are used wherever the variable font has them. This dilation is only for
drawings that live outside that font.
"""
import pathops
from fontTools.pens.recordingPen import RecordingPen

REGULAR_STEM = 60
BOLD_STEM = 105
RADIUS = (BOLD_STEM - REGULAR_STEM) / 2


def expand_path(path, radius, stretch=64):
    """Dilation by a horizontal segment, via a uniform offset in stretched space."""
    if radius <= 0:
        return path
    scaled = path.transform(1, 0, 0, stretch, 0, 0)
    stroked = pathops.Path()
    stroked.addPath(scaled)
    stroked.stroke(radius * 2, pathops.LineCap.ROUND_CAP, pathops.LineJoin.ROUND_JOIN, 2.0)
    stroked.convertConicsToQuads(0.4)
    expanded = pathops.op(scaled, stroked, pathops.PathOp.UNION)
    return expanded.transform(1, 0, 0, 1 / stretch, 0, 0)


def _runs(path, y):
    spans, inside, start = [], False, None
    bounds = path.bounds
    for x in range(int(bounds[0]) - 2, int(bounds[2]) + 3):
        hit = path.contains((x + 0.5, y))
        if hit and not inside:
            start, inside = x, True
        elif not hit and inside:
            spans.append(x - start)
            inside = False
    return spans


def vertical_stem(path):
    """Median of the narrow horizontal runs through the middle of the outline."""
    bounds = path.bounds
    height = bounds[3] - bounds[1]
    width = bounds[2] - bounds[0]
    if height < 40 or width < 20:
        return None
    samples = []
    y0 = int(bounds[1] + height * 0.3)
    y1 = int(bounds[1] + height * 0.7)
    for y in range(y0, y1, 10):
        stems = [span for span in _runs(path, y) if 12 <= span <= width * 0.5]
        if stems:
            samples.append(min(stems))
    if not samples:
        return None
    samples.sort()
    return samples[len(samples) // 2]


def radius_for(path):
    """Radius that scales this outline's stem by the Regular-to-Bold ratio."""
    stem = vertical_stem(path)
    if stem is None:
        return RADIUS
    return max(0.0, min(40.0, (stem * BOLD_STEM / REGULAR_STEM - stem) / 2))


def outline_path(outline, glyf):
    path = pathops.Path()
    outline.draw(path.getPen(), glyf)
    return path


def expand_outline(outline, glyf, make_glyph, radius=None):
    path = outline_path(outline, glyf)
    if radius is None:
        radius = radius_for(path)
    if radius < 0.5:
        return outline
    expanded = expand_path(path, radius)
    recording = RecordingPen()
    expanded.draw(recording)
    return make_glyph([recording])
