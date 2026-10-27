"""Fit angular reversals supported by straight incoming/outgoing strokes."""

import numpy as np


def sharpen(paths, mask, scale, pad, base):
    output = []
    for points in paths:
        arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
        candidates = []
        for at in np.arange(90, arc[-1] - 90, 10):
            a, b, c, d = [
                int(np.searchsorted(arc, at + offset)) for offset in (-85, -40, 40, 85)
            ]
            first = points[a : b + 1]
            last = points[c : d + 1]
            p = first.mean(axis=0)
            q = last.mean(axis=0)
            vi = first[-1] - first[0]
            vo = last[-1] - last[0]
            vi /= max(np.linalg.norm(vi), 1)
            vo /= max(np.linalg.norm(vo), 1)
            dot = np.dot(vi, vo)
            if dot > -0.4 or min(abs(vi[1]), abs(vo[1])) > 0.08:
                continue
            matrix = np.column_stack([vi, -vo])
            if abs(np.linalg.det(matrix)) < 0.1:
                continue
            t, u = np.linalg.solve(matrix, q - p)
            if t < 0 or u > 0:
                continue
            corner = p + t * vi
            pivot = points[int(np.searchsorted(arc, at))]
            if np.linalg.norm(corner - pivot) > 90:
                continue
            y, x = round(base - corner[1] * scale), round(pad + corner[0] * scale)
            if not (0 <= y < len(mask) and 0 <= x < len(mask[0]) and mask[y, x]):
                continue
            fit1 = np.abs((first - p) @ np.array([-vi[1], vi[0]])).mean()
            fit2 = np.abs((last - q) @ np.array([-vo[1], vo[0]])).mean()
            if max(fit1, fit2) > 3:
                continue
            candidates.append((fit1 + fit2, at, b, c, corner))
        taken = []
        for candidate in sorted(candidates, key=lambda c: c[0]):
            if any(abs(candidate[1] - c[1]) < 140 for c in taken):
                continue
            taken.append(candidate)
        new = []
        start = 0
        for _, at, b, c, corner in sorted(taken, key=lambda c: c[1]):
            new.extend(points[start : b + 1])
            new.append(corner)
            start = c
        new.extend(points[start:])
        output.append(np.asarray(new))
    return output
