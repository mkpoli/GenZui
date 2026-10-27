"""Fit bounded straight segments and cubic curves to learned glyph outlines."""

from itertools import pairwise

import aggdraw
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, label
from scipy.spatial import cKDTree
from skimage.measure import find_contours


def unit(vector):
    return vector / max(float(np.linalg.norm(vector)), 1e-10)


def resample(points, step=0.5):
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    count = max(12, int(np.ceil(lengths[-1] / step)))
    positions = np.linspace(0, lengths[-1], count, endpoint=False)
    return np.column_stack(
        [np.interp(positions, lengths, points[:, axis]) for axis in (0, 1)]
    )


def fit_segment(points, left, right, tolerance):
    """Least-squares cubic handles with recursive residual-based subdivision."""
    chord = points[-1] - points[0]
    length = float(np.linalg.norm(chord))
    if len(points) < 3 or length < 1e-6:
        return [("L", points[-1])]
    u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    u /= max(u[-1], 1e-10)
    projection = (points - points[0]) @ unit(chord)
    line_error = np.linalg.norm(
        points - (points[0] + projection[:, None] * unit(chord)), axis=1
    )
    if (
        length >= 5
        and line_error.max() <= tolerance
        and projection.min() >= -tolerance
        and projection.max() <= length + tolerance
    ):
        return [("L", points[-1])]
    b = np.column_stack([(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u**3])
    basis = np.stack([b[:, 1, None] * left, b[:, 2, None] * right], axis=-1)
    residual = (
        points
        - (b[:, 0] + b[:, 1])[:, None] * points[0]
        - (b[:, 2] + b[:, 3])[:, None] * points[-1]
    )
    handles, *_ = np.linalg.lstsq(basis.reshape(-1, 2), residual.ravel(), rcond=None)
    if (
        not np.isfinite(handles).all()
        or handles.min() <= 0
        or handles.max() > length * 1.5
    ):
        handles = np.full(2, length / 3)
    control = np.array(
        [
            points[0],
            points[0] + left * handles[0],
            points[-1] + right * handles[1],
            points[-1],
        ]
    )
    error = np.linalg.norm(b @ control - points, axis=1)
    if error.max() <= tolerance or len(points) <= 3:
        return [("C", control[1:])]
    split = int(np.clip(np.argmax(error), 1, len(points) - 2))
    tangent = unit(points[min(split + 2, len(points) - 1)] - points[max(0, split - 2)])
    return fit_segment(points[: split + 1], left, -tangent, tolerance) + fit_segment(
        points[split:], tangent, right, tolerance
    )


def fit_contour(points, strength):
    sampled = resample(points)
    smooth = gaussian_filter1d(sampled, strength / 0.5, axis=0, mode="wrap")
    # Anchors spaced by arc length avoid a special start/end kink.
    anchors = np.linspace(0, len(smooth), 5, dtype=int)
    closed = np.vstack([smooth, smooth[0]])
    commands = [("M", smooth[0])]
    for start, end in pairwise(anchors):
        left = unit(
            smooth[(start + 2) % len(smooth)] - smooth[(start - 2) % len(smooth)]
        )
        right = -unit(smooth[(end + 2) % len(smooth)] - smooth[(end - 2) % len(smooth)])
        commands.extend(
            fit_segment(closed[start : end + 1], left, right, strength * 0.7)
        )
    commands.append(("Z", None))
    return commands


def points_for(commands):
    points = []
    current = None
    for op, value in commands:
        if op == "M":
            current = value
            points.append(value)
        elif op == "L":
            n = max(2, int(np.ceil(np.linalg.norm(value - current) * 4)))
            points.extend(np.linspace(current, value, n)[1:])
            current = value
        elif op == "C":
            controls = np.vstack([current, value])
            n = max(
                3,
                int(
                    np.ceil(np.linalg.norm(np.diff(controls, axis=0), axis=1).sum() * 4)
                ),
            )
            u = np.linspace(0, 1, n)
            b = np.column_stack(
                [(1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u**3]
            )
            points.extend((b @ controls)[1:])
            current = value[-1]
    return np.array(points)


def raster(contours, scale=2):
    image = Image.new("L", (256 * scale, 256 * scale))
    path = aggdraw.Path()
    for commands in contours:
        for op, value in commands:
            if op == "M":
                path.moveto(*(value * scale))
            elif op == "L":
                path.lineto(*(value * scale))
            elif op == "C":
                path.curveto(*(value * scale).ravel())
            else:
                path.close()
    draw = aggdraw.Draw(image)
    # A brush-only aggdraw path expands by 0.5 units. A zero-width pen
    # selects the original fill contour without adding a visible stroke.
    draw.path(path, aggdraw.Pen(255, 0), aggdraw.Brush(255))
    draw.flush()
    return np.asarray(image)


def region_labels(mask):
    ink, nink = label(mask, np.ones((3, 3)))
    white, _ = label(~mask)
    exterior = np.unique(np.r_[white[0], white[-1], white[:, 0], white[:, -1]])
    holes = white.copy()
    holes[np.isin(white, exterior)] = 0
    return ink, nink, holes, len(np.unique(holes)) - 1


def same_regions(original, candidate):
    """Require one-to-one overlap of every ink component and enclosed counter."""
    a, na, ah, nha = region_labels(original)
    b, nb, bh, nhb = region_labels(candidate)
    if (na, nha) != (nb, nhb):
        return False
    for first, second in ((a, b), (ah, bh)):
        pairs = np.unique(np.column_stack([first.ravel(), second.ravel()]), axis=0)
        pairs = pairs[(pairs[:, 0] > 0) & (pairs[:, 1] > 0)]
        if (
            len(pairs) != len(np.unique(first)) - 1
            or len(pairs) != len(np.unique(second)) - 1
        ):
            return False
        if len(np.unique(pairs[:, 0])) != len(pairs) or len(
            np.unique(pairs[:, 1])
        ) != len(pairs):
            return False
    return True


def path_text(contours):
    parts = []
    for commands in contours:
        for op, value in commands:
            if op == "Z":
                parts.append("Z")
            else:
                parts.append(op + " ".join(f"{v:.3f}" for v in value.ravel()))
    return "".join(parts)


def clean(field):
    field = np.asarray(field)
    if field.shape != (256, 256) or not np.isfinite(field).all():
        raise ValueError("Expected a finite 256 by 256 field")
    source = [
        c[:, ::-1] - 0.5
        for c in find_contours(
            np.pad(field, 1, constant_values=-1), 0, fully_connected="high"
        )
    ]
    raw = [[("M", p[0]), *[("L", xy) for xy in p[1:]], ("Z", None)] for p in source]
    if not source:
        return (
            "",
            np.zeros((256, 256), dtype=np.uint8),
            {
                "strength": 0,
                "source_iou": 1.0,
                "max_sampled_boundary_shift_px": 0.0,
                "raw_segments": 0,
                "segments": 0,
                "lines": 0,
                "curves": 0,
                "fallback": True,
            },
        )
    reference = raster(raw) >= 128
    native_reference = raster(raw, 1) >= 128
    source_cloud = np.concatenate([resample(p, 0.25) for p in source])
    tree = cKDTree(source_cloud)
    for strength in (1.0, 0.65, 0.4, 0.2):
        candidate = [fit_contour(p, strength) for p in source]
        # Check exactly the coordinates serialized into the SVG.
        candidate = [
            [
                (op, np.round(value, 3) if value is not None else None)
                for op, value in contour
            ]
            for contour in candidate
        ]
        cloud = np.concatenate([points_for(c) for c in candidate])
        distance = max(
            tree.query(cloud)[0].max(), cKDTree(cloud).query(source_cloud)[0].max()
        )
        if distance > 1.1:
            continue
        mask = raster(candidate) >= 128
        iou = (mask & reference).sum() / max(1, (mask | reference).sum())
        if (
            iou < 0.94
            or not same_regions(reference, mask)
            or not same_regions(native_reference, raster(candidate, 1) >= 128)
        ):
            continue
        return (
            path_text(candidate),
            raster(candidate, 1),
            {
                "strength": strength,
                "source_iou": float(iou),
                "max_sampled_boundary_shift_px": float(distance),
                "raw_segments": sum(len(c) - 2 for c in raw),
                "segments": sum(len(c) - 2 for c in candidate),
                "lines": sum(op == "L" for c in candidate for op, _ in c),
                "curves": sum(op == "C" for c in candidate for op, _ in c),
                "fallback": False,
            },
        )
    return (
        path_text(raw),
        raster(raw, 1),
        {
            "strength": 0,
            "source_iou": 1.0,
            "max_sampled_boundary_shift_px": 0.0,
            "raw_segments": sum(len(c) - 2 for c in raw),
            "segments": sum(len(c) - 2 for c in raw),
            "lines": sum(len(c) - 2 for c in raw),
            "curves": 0,
            "fallback": True,
        },
    )
