"""Reopen substantial source counters and locally blocked white corridors."""

import aggdraw
import numpy as np
import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.roundingPen import RoundingPen
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, label
from skimage.graph import MCP_Geometric
from skimage.measure import approximate_polygon, find_contours


def signed_area(shape):
    pen = AreaPen(None)
    shape.draw(pen)
    return pen.value


def preserve_white(shape, mask, scale, pad, base, width, RasterPen):
    # Repair only a substantial counter, never the complete whitespace graph.
    white = ~mask
    source_labels, count = label(white)
    source_outside = source_labels[0, 0]
    significant = [
        i
        for i in range(1, count + 1)
        if i != source_outside
        and np.count_nonzero(source_labels == i) >= 2000 * scale**2
    ]
    output_counters = [c for c in shape.contours if signed_area(c) < -2000]
    distance = None
    guard = np.zeros_like(mask)
    image = Image.new("L", (mask.shape[1], mask.shape[0]))
    pen = RasterPen(pad, base)
    shape.draw(pen)
    context = aggdraw.Draw(image)
    context.path(pen.path, aggdraw.Brush(255))
    context.flush()
    output_white = np.asarray(image) <= 127
    for i in significant:
        if distance is None:
            distance = distance_transform_edt(white)
        counter = source_labels == i
        y, x = np.unravel_index(np.argmax(np.where(counter, distance, 0)), mask.shape)
        if (
            shape.contains(((x - pad) / scale, (base - y) / scale))
            or np.count_nonzero(counter & output_white) < counter.sum() * 0.35
        ):
            guard |= counter & (distance >= max(1, distance[counter].max() * 0.3))
    if output_counters:
        output_labels, n = label(output_white)
        output_outside = output_labels[0, 0]
        if distance is None:
            distance = distance_transform_edt(white)
        destination = (
            white & (output_labels == output_outside) & (distance >= 3 * scale)
        )
        for i in range(1, n + 1):
            if i == output_outside:
                continue
            counter = output_labels == i
            if counter.sum() < 2000 * scale**2:
                continue
            candidate = counter & (source_labels == source_outside)
            if candidate.sum() < counter.sum() * 0.5:
                continue
            seed = np.unravel_index(
                np.argmax(np.where(candidate, distance, 0)), mask.shape
            )
            costs = np.where(
                distance >= 2 * scale,
                1 + 100 / (distance + 1) ** 2 + 4 * (~output_white),
                np.inf,
            )
            solver = MCP_Geometric(costs)
            cost, _ = solver.find_costs([seed])
            end = np.unravel_index(
                np.argmin(np.where(destination, cost, np.inf)), mask.shape
            )
            if not np.isfinite(cost[end]):
                continue
            route = solver.traceback(end)
            corridor = Image.new("L", image.size)
            ImageDraw.Draw(corridor).line(
                [(x, y) for y, x in route], fill=255, width=max(3, round(20 * scale))
            )
            guard |= (np.asarray(corridor) > 127) & white
    if not guard.any():
        return shape
    path = pathops.Path()
    path.fillType = pathops.FillType.EVEN_ODD
    for contour in find_contours(np.pad(guard, 1), 0.5):
        contour = approximate_polygon(contour, 0.5)
        points = [((x - 1 - pad) / scale, (base - (y - 1)) / scale) for y, x in contour]
        if len(points) < 3:
            continue
        path.moveTo(*points[0])
        for p in points[1:]:
            path.lineTo(*p)
        path.close()
    rounded = []
    for source in (shape, path):
        target = pathops.Path()
        target.fillType = source.fillType
        source.draw(
            RoundingPen(target.getPen(), roundFunc=lambda value: round(value * 4) / 4)
        )
        rounded.append(target)
    return pathops.op(rounded[0], rounded[1], pathops.PathOp.DIFFERENCE)
