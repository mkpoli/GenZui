"""Draft a Bold master for a drawn Regular stroke.

GenZui's drawn strokes carry a Regular and a Bold master with the same
commands and points. This tool proposes the Bold one. It measures the local
stroke width along the Regular outline (the largest inscribed circle touching
each point) and moves the outline outward by the weight Noto Serif JP gains
there from wght 400 to 700: about 1.72 times for strokes up to 60 units,
easing to 1.5 times for the heaviest. Ends and tips stay close to their
Regular size, and counters shrink as the ink grows. Anchors move once, along
the bisector of their two normals; handles are refit to the offset outline.

The result is a starting point. Terminals, joins and counters are then
corrected by eye and the finished master is written into the source.

    python scripts/draft_bold.py 'M221 500 C366 526 ... Z'
"""
import re
import sys
from math import hypot

import numpy as np
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
from PIL import Image, ImageChops, ImageDraw
from scipy.spatial import cKDTree
from skimage.morphology import medial_axis

ARITY = {'M': 2, 'L': 2, 'Q': 4, 'C': 6, 'Z': 0}
X0, Y0, SIZE = -300, -400, 1700


def parse(d):
    tokens = re.findall(r'[MLQCZ]|-?\d*\.?\d+(?:e-?\d+)?', d)
    commands, i, last = [], 0, None
    while i < len(tokens):
        c = tokens[i]
        if c.isalpha():
            i += 1
        else:  # An implicit repeat; a repeated moveto is a lineto.
            c = 'L' if last == 'M' else last
        last = c
        commands.append([c, [float(v) for v in tokens[i:i + ARITY[c]]]])
        i += ARITY[c]
    return commands


def unparse(commands):
    def number(v):
        return '%d' % round(v) if abs(v - round(v)) < .26 else '%.1f' % v
    return ' '.join(c + ' '.join(number(v) for v in values) for c, values in commands)


def glyph_path(glyphs, name):
    """A glyph outline as explicit M, L, Q, C and Z commands."""
    pen = RecordingPen()
    glyphs[name].draw(pen)
    path = pathops.Path()
    pen.replay(path.getPen())
    commands = []
    for verb, points in path.segments:
        letter = {'moveTo': 'M', 'lineTo': 'L', 'qCurveTo': 'Q', 'curveTo': 'C',
                  'closePath': 'Z', 'endPath': 'Z'}[verb]
        if letter == 'Q' and len(points) > 2:
            # Split a TrueType run into quadratics at implied on-curve points.
            for a, b in zip(points[:-2], points[1:-1]):
                commands.append(['Q', [*a, (a[0]+b[0])/2, (a[1]+b[1])/2]])
            points = points[-2:]
        commands.append([letter, [v for point in points for v in point]])
    return unparse(commands)


def shape(d):
    pen = RecordingPen()
    parse_path(d, pen)
    result = pathops.Path()
    pen.replay(result.getPen())
    return pathops.simplify(result)


def flatten(path, steps=16):
    polygons, current, point = [], [], None
    for verb, points in path.segments:
        if verb == 'moveTo':
            current = [points[0]]
            point = points[0]
        elif verb == 'lineTo':
            current.append(points[0])
            point = points[0]
        elif verb == 'curveTo':
            p = np.array([point, *points])
            current.extend(tuple(bezier(p, t)) for t in np.linspace(0, 1, steps + 1)[1:])
            point = points[-1]
        elif verb == 'qCurveTo':
            # A TrueType run: implied on-curve points between off-curve pairs.
            offs = list(points[:-1])
            if points[-1] is None:  # A contour with no on-curve point.
                offs = list(points[:-1])
                point = tuple((a + b) / 2 for a, b in zip(offs[-1], offs[0]))
                points = (*offs, point)
                current = [point]
            for k, control in enumerate(offs):
                end = points[-1] if k == len(offs) - 1 else tuple(
                    (a + b) / 2 for a, b in zip(control, offs[k + 1]))
                p = np.array([point, control, end])
                current.extend(tuple(bezier(p, t)) for t in np.linspace(0, 1, steps + 1)[1:])
                point = end
        elif verb in ('closePath', 'endPath'):
            if len(current) > 2:
                polygons.append(current)
            current = []
    return polygons


def mask(path):
    image = Image.new('1', (SIZE, SIZE), 0)
    for polygon in flatten(path):
        layer = Image.new('1', (SIZE, SIZE), 0)
        ImageDraw.Draw(layer).polygon(
            [(x - X0, SIZE - (y - Y0)) for x, y in polygon], fill=1)
        image = ImageChops.logical_xor(image, layer)
    return np.array(image, dtype=bool)


def bezier(p, t):
    if len(p) == 2:
        return (1 - t) * p[0] + t * p[1]
    if len(p) == 3:
        return (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * p[1] + t * t * p[2]
    return ((1 - t) ** 3 * p[0] + 3 * (1 - t) ** 2 * t * p[1]
            + 3 * (1 - t) * t * t * p[2] + t ** 3 * p[3])


def tangent(p, t):
    if len(p) == 2:
        d = p[1] - p[0]
    elif len(p) == 3:
        d = 2 * (1 - t) * (p[1] - p[0]) + 2 * t * (p[2] - p[1])
    else:
        d = (3 * (1 - t) ** 2 * (p[1] - p[0]) + 6 * (1 - t) * t * (p[2] - p[1])
             + 3 * t * t * (p[3] - p[2]))
    return d if hypot(*d) > 1e-6 else p[-1] - p[0]


def gain(width):
    ratio = 1.72 if width <= 60 else max(1.5, 1.72 - (width - 60) * .0055)
    return max(2.0, width * (ratio - 1) / 2)


class Width:
    """Stroke width at an outline point, from the shape's medial axis."""

    def __init__(self, path):
        self.path = path
        skeleton, distance = medial_axis(mask(path), return_distance=True)
        ys, xs = np.nonzero(skeleton)
        radius = distance[ys, xs]
        keep = radius > 1.5
        self.points = np.stack([xs, ys], 1)[keep].astype(float)
        self.radius = radius[keep]
        self.tree = cKDTree(self.points)
        # Circles at junctions are wider than any stroke that meets there.
        self.cap = 2 * np.percentile(self.radius, 90)

    def __call__(self, point):
        pixel = np.array([point[0] - X0, SIZE - (point[1] - Y0)])
        near = np.array(self.tree.query_ball_point(pixel, 120), dtype=int)
        if not len(near):
            return 20.0
        reach = np.hypot(*(self.points[near] - pixel).T) - self.radius[near]
        touching = reach <= 10
        if touching.any():
            found = 2 * self.radius[near][touching].max()
        else:
            found = 2 * self.radius[near][np.argmin(reach)]
        return min(found, self.cap)


def draft_contour(d, width):
    commands = parse(d)
    segments, current, start = [], None, None
    # A zero-length segment keeps its command and follows the next anchor.
    pending, stay = [], {}
    for i, (c, values) in enumerate(commands):
        if c == 'M':
            current = start = np.array(values)
        elif c == 'Z':
            if hypot(*(current - start)) > .01:
                segments.append((None, [current, start]))
            current = start
        else:
            points = [np.array(values[j:j + 2]) for j in range(0, len(values), 2)]
            if all(hypot(*(q - current)) < .01 for q in points):
                pending.append(i)
                continue
            stay.update({j: len(segments) for j in pending})
            pending = []
            segments.append((i, [current, *points]))
            current = points[-1]
    stay.update({j: 0 for j in pending})

    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]

    area = sum(cross(bezier(p, t), bezier(p, t + .125))
               for _, p in segments for t in np.arange(0, 1, .125))
    sign = 1 if area > 0 else -1
    p = max((p for _, p in segments), key=lambda p: hypot(*(p[-1] - p[0])))
    probe = bezier(p, .5)
    d0 = tangent(p, .5)
    normal = sign * np.array([d0[1], -d0[0]]) / hypot(*d0)
    if width.path.contains(tuple(probe + normal * 1.5)):
        sign = -sign  # A counter: its outer side is ink.

    def outward(d):
        return sign * np.array([d[1], -d[0]]) / (hypot(*d) or 1)

    def offset(p, t):
        q = bezier(p, t)
        return q + outward(tangent(p, t)) * gain(width(q))

    anchors = []
    for k, (_, p) in enumerate(segments):
        before = segments[k - 1][1]
        n1, n2 = outward(tangent(before, 1)), outward(tangent(p, 0))
        bisector = (n1 + n2) / (hypot(*(n1 + n2)) or 1)
        miter = max(.5, float(bisector @ n1))
        anchors.append(p[0] + bisector * gain(width(p[0])) / miter)

    moved = {}
    ts = np.linspace(0, 1, 30)[2:-2]
    for k, (i, p) in enumerate(segments):
        if i is None:
            continue
        a0, a1 = anchors[k], anchors[(k + 1) % len(segments)]
        if len(p) == 2:
            moved[i] = [a1]
            continue
        # At a concave corner the offset runs past the new anchor; fit only
        # the stretch between the offset points nearest the two anchors.
        dense = np.linspace(0, 1, 101)
        trace = np.array([offset(p, t) for t in dense])
        t0 = dense[np.argmin(np.hypot(*(trace - a0).T))]
        t1 = dense[np.argmin(np.hypot(*(trace - a1).T))]
        if t1 - t0 < .2:
            t0, t1 = 0.0, 1.0
        target = np.array([offset(p, t0 + (t1 - t0) * t) for t in ts])
        if len(p) == 4:
            basis = np.stack([3 * (1 - ts) ** 2 * ts, 3 * (1 - ts) * ts ** 2], 1)
            rest = target - np.outer((1 - ts) ** 3, a0) - np.outer(ts ** 3, a1)
            handles = np.linalg.lstsq(basis, rest, rcond=None)[0]
            moved[i] = [handles[0], handles[1], a1]
        else:
            basis = 2 * (1 - ts) * ts
            rest = target - np.outer((1 - ts) ** 2, a0) - np.outer(ts ** 2, a1)
            moved[i] = [(basis @ rest) / (basis @ basis), a1]
    for i, (c, _) in enumerate(commands):
        if c == 'M':
            commands[i][1] = list(anchors[0])
        elif i in moved:
            commands[i][1] = [v for point in moved[i] for v in point]
        elif i in stay:
            commands[i][1] = list(anchors[stay[i]]) * (len(commands[i][1]) // 2)
    return unparse(commands)


def draft(d):
    """The Bold draft of a Regular path, with the same commands and points."""
    width = Width(shape(d))
    contours = [part.strip() for part in re.split(r'(?=M)', d) if part.strip()]
    return ' '.join(draft_contour(contour, width) for contour in contours)


if __name__ == '__main__':
    print(draft(sys.argv[1]))
