"""Regular historical forms, drawn in a 1000-unit em with baseline at zero.

Native components supply the stroke vocabulary. New joins, returns and bars
are drawn explicitly; TOMO, TOTE and TOKI have uniform optical reductions. GenSeki/Sukima and published historical specimens inform the
structure, without copying their outlines. TOMO, alternate NE and alternate WI
use Noto's Mincho kana stroke vocabulary.
"""
from math import hypot, sqrt
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

REVISED = (0x1B123, 0x1B124, 0x1B125, 0x1B126, 0x1B127, 0x1B128,
           0x2A708, 0x2CEFF, 0x2CF00, 0x2CF02)
REVISION_0104 = (0x2A708, 0x1B123, 0x2CEFF, 0x2CF02, 0x2CF00, 0x1B11F, 0x1B127, 0x1B128)
REVISION_0107 = (0x2A708, 0x2CEFF, 0x2CF02, 0x2CF00)
REVISION_0108 = (0x2CEFF, 0x1B127, 0x1B128)
REVISION_0109 = (0x1B127, 0x1B128)
REVISION_0110 = ()  # Only the unencoded Hooked WU alternate changes.
REVISION_0112 = (0x1B124, 0x1B125)
REVISION_0111 = ()  # Only the unencoded Hooked WU alternate changes.
REVISION_0106 = (0x2A708, 0x1B123, 0x2CEFF, 0x2CF02, 0x2CF00, 0x1B11F, 0x1B127, 0x1B128)
REVISION_0105 = (0x2A708, 0x2CEFF, 0x2CF02, 0x2CF00, 0x1B11F, 0x1B127, 0x1B128)
REVISION_0103 = (0x1B124, 0x2A708, 0x1B123, 0x2CEFF, 0x2CF02, 0x2CF00, 0x1B11F)


def wu_alternate(font):
    """Resolve the alternate after saving a font with a format-3 post table."""
    table = font['GSUB'].table
    feature = next(r.Feature for r in table.FeatureList.FeatureRecord if r.FeatureTag == 'ss01')
    mapping = table.LookupList.Lookup[feature.LookupListIndex[0]].SubTable[0].mapping
    return mapping[font.getBestCmap()[0x1B11F]]


def path(commands):
    pen = RecordingPen()
    parse_path(commands, pen)
    return pen


def curved_wu(part, transform):
    """Preserve KE's native curved descent, closing its stem inside HO's bar."""
    native = part('け', [0])
    stem = RecordingPen()
    stem.value = native.value[:3]
    stem.qCurveTo((693, 520), (689, 599), (684, 668))
    stem.lineTo((750, 680))
    start = next(i for i, (op, args) in enumerate(native.value)
                 if op == 'qCurveTo' and all(abs(a-b) < 1 for a, b in zip(args[-1], (754, 497))))
    stem.value.extend(native.value[start:])
    return [part('け', [1]), transform(part('け', [2]), (1, 0, 0, 1, 0, -65)),
            part('ほ', [3]), stem]


def hooked_wu_stem():
    """A compact return with a constant-width approach through the lower bend."""
    outer = ((765, 340.5), (762.877, 230.45), (735, -58), (610, -58))
    width = 62

    def curve(t):
        q = 1-t
        p = tuple(q**3*outer[0][j] + 3*q*q*t*outer[1][j] +
                  3*q*t*t*outer[2][j] + t**3*outer[3][j] for j in (0,1))
        d = tuple(3*(q*q*(outer[1][j]-outer[0][j]) +
                     2*q*t*(outer[2][j]-outer[1][j]) +
                     t*t*(outer[3][j]-outer[2][j])) for j in (0,1))
        dd = tuple(6*(q*(outer[2][j]-2*outer[1][j]+outer[0][j]) +
                      t*(outer[3][j]-2*outer[2][j]+outer[1][j])) for j in (0,1))
        speed = hypot(*d)
        normal = (d[1]/speed, -d[0]/speed)
        rate = (d[0]*dd[0]+d[1]*dd[1])/speed**2
        nd = (dd[1]/speed-normal[0]*rate, -dd[0]/speed-normal[1]*rate)
        return tuple(p[j]+width*normal[j] for j in (0,1)), tuple(d[j]+width*nd[j] for j in (0,1))

    # Meet the original upper quadratic at the same height as the offset.
    start, _ = curve(0)
    cut = (680-sqrt(680**2-280*(660-start[1])))/140
    upper_control = (650+112*cut, 660-340*cut)
    upper_end = (650+224*cut-236*cut*cut, start[1])
    correction = upper_end[0]-start[0]

    def inner(t):
        p, d = curve(t)
        p = (p[0]+correction*(1-t)**3, p[1])
        d = (d[0]-3*correction*(1-t)**2, d[1])
        if t == 0:
            tangent = (upper_end[0]-upper_control[0], upper_end[1]-upper_control[1])
            factor = hypot(*d)/hypot(*tangent)
            d = (factor*tangent[0], factor*tangent[1])
        return p, d

    stem = path('M650 660 L712 672 Q768 496 765 340.5 '
                'C762.877 230.45 735 -58 610 -58 '
                'C586 -58 582 -27 569 -6 C559 11 548 31 536 60 '
                'L548 76 C565 52 592 4 610 4')
    if stem.value[-1][0] == 'endPath':
        stem.value.pop()
    # Cubic Hermite segments follow the analytic inward offset. Their shared
    # positions and tangents avoid a pinched join between stem and return.
    for i in range(16, 0, -1):
        t0, t1 = i/16, (i-1)/16
        p0, d0 = inner(t0); p1, d1 = inner(t1)
        step = (t1-t0)/3
        stem.curveTo(tuple(p0[j]+step*d0[j] for j in (0,1)),
                     tuple(p1[j]-step*d1[j] for j in (0,1)), p1)
    stem.qCurveTo(upper_control, (650, 660))
    stem.closePath()
    return stem


def hooked_wu(part, transform):
    """One broad outward arc flows through a compact drawn return."""
    return [part('け', [1]), path(
            'M451 697 L465 711 C500 687 539 680 580 684 '
            'C633 688 711 700 769 713 C794 719 816 729 824 729 '
            'C847 729 872 717 872 700 C873 687 863 679 854 674 '
            'C799 655 672 635 593 634 C532 632 483 651 451 697 Z'), path(
            'M412 476 L426 490 C475 462 518 450 577 452 '
            'C646 454 747 472 811 492 C836 500 856 516 866 516 '
            'C888 516 917 504 917 489 C917 473 909 466 889 458 '
            'C819 434 683 406 580 406 C509 406 451 427 412 476 Z'),
            hooked_wu_stem()]


def reshape(outline, point):
    """Move contour control points without altering the other components."""
    result = RecordingPen()
    result.value = [(op, tuple(None if p is None else point(*p) for p in args))
                    for op, args in outline.value]
    return result


def koto_entry_point(x, y, amount):
    t = max(0, min(1, (610-x)/351))
    return x, y - amount*t*t*(3-2*t) if y >= 700 else y


def balanced_koto(parts):
    """Accepted E: lower and shift the upper curve, extend the rising stroke."""
    def smooth(t):
        t = max(0, min(1, t))
        return t*t*(3-2*t)
    def upper(x, y):
        px, py = koto_entry_point(x, y, 44)
        blend = smooth((y-350)/210)
        return px-22*blend, py-40*blend
    def lower(x, y):
        blend = smooth((y-250)/150)*smooth((x-460)/150)
        return x+72*blend, y+24*blend
    return [reshape(parts[0], lower), reshape(parts[1], upper)]


def wi_left_point(x, y):
    # Move the foot inward without changing its height. The centre follows
    # NA's native descent; contracting about it thins both sides equally.
    t = max(0, min(1, (350-y)/399))
    centre = 465 - 120*t*t
    return centre + (x-centre)*.88 + 90*t*t


def hiragana_nari(part):
    """Native N brush entry, diagonal and foot, joined to NARI's low wave."""
    native = part('ん', [0])
    outline = path(
        'M235 198 C272 240 309 266 344 266 C386 266 420 241 465 202 '
        'C521 152 578 33 659 33')
    # E's native lower return supplies a full-width rising finish and terminal.
    # Translate it by (-20, -4); its bottom becomes -32, matching N.
    tail = part('え', [0])
    if outline.value[-1][0] == 'endPath':
        outline.value.pop()
    tail_start = next(i for i, (op,args) in enumerate(tail.value)
                      if op == 'qCurveTo' and abs(args[-1][0]-848)<1 and abs(args[-1][1]-57)<1)
    for op,args in tail.value[tail_start:-1]:
        getattr(outline, op)(*((x-20, y-4) for x,y in args))
    outline.curveTo((607,-32), (557,20), (520,69))
    outline.curveTo((475,114), (428,186), (382,205))
    outline.curveTo((350,220), (308,223), (280,204))
    outline.curveTo((260,190), (245,176), (235,165))
    # Continue the contour through N's foot and upper stroke. Its original
    # high shoulder and lower loop are replaced by the drawn low wave.
    if outline.value[-1][0] == 'endPath':
        outline.value.pop()
    outline.value.extend(native.value[5:17])
    outline.curveTo((306, 308), (266, 249), (235, 198))
    outline.closePath()
    return [outline]


def tomo_entry_point(x, y):
    t = max(0, min(1, (350-x)/149))
    return x+18*t*t, y-35*t*t


def refinements(part, transform):
    def move(outline, x=0, y=0):
        return transform(outline, (1, 0, 0, 1, x, y))

    # One native TO stem, at its original width, shared by TOKI and TOTE.
    stem = move(part('ト', [0]), -220)
    forms = {
        # Curved WU is the default; the hooked form is added as ss01.
        0x1B11F: curved_wu(part, transform),
        # The lower bowl is shallower; the upper connector gains room and
        # a lighter inner curve without changing the top bar's weight.
        0x1B123: [transform(part('と', [0]), (1, 0, 0, .84, 0, -4.32)), path(
            'M259 773 L276 794 C313 771 370 753 426 753 '
            'C482 753 546 763 605 774 C634 780 660 790 677 790 '
            'C701 790 738 773 751 752 C762 735 751 720 727 715 '
            'C654 699 601 670 564 636 C522 597 497 550 495 502 '
            'C493 451 513 411 551 383 L506 356 '
            'C467 394 439 443 441 496 C438 561 476 616 537 670 '
            'C556 687 578 710 598 727 C536 716 468 706 418 706 '
            'C350 706 295 738 259 773 Z')],

        # A shear makes KI more upright while keeping width at each height.
        # The two crossbars start inside the shared
        # left stem, eliminating an accidental gap or a touching-only join.
        0x1B124: [stem, transform(part('キ', [0]), (1, 0, .075, 1, 60, 0)), path(
            'M221 500 C366 526 567 574 700 611 '
            'C739 622 764 634 785 636 C816 639 855 627 863 609 '
            'C871 591 856 581 827 575 C701 552 438 490 222 449 Z'), path(
            'M222 265 C382 300 611 352 792 402 '
            'C821 410 841 421 863 421 C896 423 933 409 940 393 '
            'C947 374 933 364 906 361 C697 338 450 268 222 211 Z')],

        # TE keeps the native top bar and descending sweep. The main bar has
        # its own full-width geometry, with a clean join to the same TO stem.
        0x1B125: [stem, move(part('テ', [2]), 80),
                  move(part('テ', [0]), 120), path(
            'M221 462 C377 476 624 504 760 519 '
            'C807 524 834 538 850 538 C883 538 925 519 938 501 '
            'C950 483 946 463 926 460 C900 457 867 469 814 468 '
            'C647 468 418 436 222 408 Z')],

        # Shortened YO bars, drawn at text weight; RI's left stroke is native
        # size and its right stroke is redrawn with a full-width descending arc.
        0x1B126: [path(
            'M109 676 L129 684 C150 655 165 633 190 633 '
            'C251 634 369 649 423 657 C442 660 451 674 466 674 '
            'C488 674 542 636 549 617 C554 603 536 591 532 570 '
            'C523 467 513 258 506 108 L447 109 '
            'C452 254 463 477 468 597 C470 607 464 611 453 610 '
            'C373 604 285 591 218 579 C196 575 187 565 174 565 '
            'C149 565 118 608 113 632 Z'), path(
            'M130 419 L149 430 C173 400 188 381 210 381 '
            'C281 384 383 398 491 407 L488 354 '
            'C380 346 293 333 232 321 C214 317 202 310 188 310 '
            'C163 310 137 351 134 380 Z'), path(
            'M98 166 L116 177 C141 145 157 126 182 126 '
            'C251 128 384 147 455 152 C484 154 518 138 523 120 '
            'C528 103 516 87 495 87 C475 87 451 95 420 95 '
            'C342 92 263 79 213 68 C194 64 182 56 168 56 '
            'C142 56 108 99 104 126 Z'),
            move(part('リ', [1]), 333), path(
            'M754 731 C779 740 803 748 825 748 '
            'C849 748 902 725 923 702 C944 681 919 668 915 633 '
            'C912 571 914 474 909 402 C904 234 831 83 669 -48 '
            'L650 -30 C780 111 835 248 840 406 '
            'C843 484 846 585 844 653 C843 677 835 691 819 697 '
            'C802 705 778 708 754 712 Z')],

        # NE's upper turn and return are drawn as kana strokes. The crossbar
        # comes from native WI, with its brush entry and rising line intact.
        0x1B127: [path(
            'M223 710 L240 722 C258 699 274 682 303 683 '
            'C406 691 577 709 689 723 C710 727 721 742 735 742 '
            'C752 742 787 721 796 708 C805 694 790 685 774 674 '
            'C708 621 626 560 533 509 L513 531 '
            'C585 583 651 641 696 695 '
            'C586 676 449 652 329 631 C308 627 294 615 280 615 '
            'C261 631 237 654 229 672 Z'), path(
            'M483 526 C495 541 518 547 537 551 '
            'L550 522 C543 496 542 472 542 447 '
            'L542 76 C542 15 531 -14 510 -29 '
            'C492 -42 476 -45 457 -40 C443 -35 439 -25 428 -16 '
            'C406 6 372 25 331 44 L342 64 '
            'C385 43 421 30 457 25 C477 23 483 36 483 57 '
            'C484 163 484 295 483 429 C483 469 483 496 483 526 Z'),
            move(reshape(part('ヰ', [3]),
                         lambda x, y: (x - max(0, 483-x)*.20, y)), 0, -150)],

        # WI uses the modern WI bars and right stem. NA supplies a full-width
        # descending left stroke. The bars move closer without any scaling.
        0x1B128: [move(reshape(part('ナ', [0]),
                           lambda x, y: (wi_left_point(x, y), y)), -122),
                  move(part('ヰ', [0]), 52),
                  move(part('ヰ', [3]), 0, -22),
                  move(part('ヰ', [2]), 0, 30)],

        # TOMO keeps MO's shoulder and return. Lengthen the intervening
        # shaft, leaving each end at native weight.
        0x2A708: [stem, move(reshape(part('モ', [2]), tomo_entry_point), 90, 82),
                  reshape(part('モ', [0]), lambda x, y:
                          (x+90, y-42+124*max(0, min(1, (y-180)/310)))), path(
            'M220 390 C410 405 649 435 791 454 '
            'C822 458 839 467 855 466 C885 465 928 445 938 426 '
            'C949 406 935 391 915 391 C881 391 854 399 821 399 '
            'C636 396 403 360 220 336 Z')],

        # Retain SHI’s enlarged dot length, with 104% transverse weight to match NO.
        0x2CF00: [transform(part('ノ'), (1, 0, .12, 1.06, 3, 0)),
                  transform(part('シ', [1]), (1.12, -.04, -.04, 1.06, 194.54, 49.08))],

        # Keep a substantial entry and neck, with a lighter bowl and a shoulder
        # moved inward to balance the long lower sweep. SHI is unchanged.
        0x2CEFF: [move(part('シ', [2]), -51, -14), path(
            'M155 384 L161 424 C193 442 235 453 266 442 '
            'C306 428 324 390 346 347 C385 269 425 202 490 162 '
            'C554 124 627 105 715 105 C772 105 822 112 865 122 '
            'C889 129 911 117 918 101 C925 84 913 71 893 65 '
            'C840 50 780 42 715 42 C607 42 519 60 452 101 '
            'C372 150 334 229 308 300 C288 354 281 380 257 391 '
            'C232 402 193 383 155 384 Z')],

        # NARI retains the Japanese chart's long diagonal. N's brush entry
        # and rounded foot supply its Mincho weight variation.
        0x2CF02: hiragana_nari(part),
    }
    # Reduce both TOMO components together, preserving their shared proportion.
    forms[0x2A708] = [transform(p, (.92, 0, 0, .92, 40, 29.2)) for p in forms[0x2A708]]
    # Match TOMO's optical footprint around the same (500, 365) centre.
    # TOKI has denser crossing strokes and uses a slightly smaller size.
    for cp, scale in ((0x1B125, .92), (0x1B124, .90)):
        forms[cp] = [transform(p, (scale, 0, 0, scale,
                                  500*(1-scale), 365*(1-scale))) for p in forms[cp]]
    forms[0x1B123] = balanced_koto(forms[0x1B123])
    return forms


DESCRIPTIONS = {
    0x1B11F: 'Curved WU preserves the native KE descent. Stylistic set 1 keeps the upper outward bow and carries its weight through a compact rounded return, set farther right.',
    0x1B123: 'KOTO E: a lower upper curve shifted left, with a longer rising right stroke and a shallow Noto TO bowl.',
    0x1B124: 'Noto TO stem and an upright KI diagonal with joined crossbars, at 90% optical size beside TOMO and TOTE.',
    0x1B125: 'Noto Serif JP TO stem and TE strokes with a drawn connecting bar, at 92% optical size beside TOMO.',
    0x1B126: 'Noto Serif JP RI short stroke; redrawn YO bars and full-weight RI descending stroke.',
    0x1B127: 'A modulated upper bar and lighter return above a hooked stem. The middle crossbar sits halfway between its 0.107 and 0.108 positions.',
    0x1B128: 'Noto WI bars join a NA-derived left descent and the native right stem. Stem spacing is halfway between 0.107 and 0.108; stroke weights are preserved.',
    0x2A708: 'Native MO stem and return beside TO. MO’s upturned entry is lower and shorter, giving the nearby TO head more space. The shared 92% optical size is unchanged.',
    0x2CF00: 'An enlarged SHI dot meets the NO-derived descent directly. Its transverse weight is closer to NO while its length is unchanged.',
    0x2CEFF: 'Native SHI upper stroke with a substantial lower entry and neck. The shoulder sits farther inward and the bowl has less weight.',
    0x2CF02: 'Redrawn NARI retains its upper stroke and rounded foot. The lower wave has steadier weight and Noto E’s full, rounded finish.',
}
