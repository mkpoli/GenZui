"""Historical forms, drawn in a 1000-unit em with baseline at zero.

Native components supply the stroke vocabulary. New joins, returns and bars
are drawn explicitly; TOMO, TOTE and TOKI have uniform optical reductions. GenSeki/Sukima and published historical specimens inform the
structure, without copying their outlines. TOMO, alternate NE and alternate WI
use Noto's Mincho kana stroke vocabulary.

Every drawn stroke has a Regular and a Bold master with the same points. Bold
takes its native strokes from Noto Serif JP at wght 700, and its drawn strokes
match that weight; scripts/draft_bold.py drafts a Bold master for review.
YORI packs two kana into one cell, so Bold draws it lighter: its native RI
stroke comes from wght 650 and its drawn strokes blend between the masters.
"""
import re
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
REVISION_0115 = (0x2A708, 0x1B124, 0x1B125, 0x1B126)
REVISION_0117 = (0x2A708,)
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


# Curved WU: KE's descent rises through a drawn left edge into HO's bar and
# returns to KE's shoulder, segment 10 of the contour in both masters.
CURVED_WU_BRIDGE = {
    False: ((693, 520), (689, 599), (684, 668), (750, 680)),
    True: ((672, 512), (668, 599), (663, 668), (769, 680)),
}


def curved_wu(part, transform, bold=False):
    """Preserve KE's native curved descent, closing its stem inside HO's bar."""
    native = part('け', [0])
    *curve, corner = CURVED_WU_BRIDGE[bold]
    stem = RecordingPen()
    stem.value = native.value[:3]
    stem.qCurveTo(*curve)
    stem.lineTo(corner)
    stem.value.extend(native.value[10:])
    return [part('け', [1]), transform(part('け', [2]), (1, 0, 0, 1, 0, -65)),
            part('ほ', [3]), stem]


# Hooked WU masters. The stem's inner edge is a constant-width offset of the
# outer arc, joined at the stem's height to the quadratic (top, upper).
HOOKED_WU = {
    False: {
        'width': 62,
        'outer': ((765, 340.5), (762.877, 230.45), (735, -58), (610, -58)),
        'top': (650, 660), 'upper': ((762, 320), (638, 50)),
        'stem': ('M650 660 L712 672 Q768 496 765 340.5 '
                 'C762.877 230.45 735 -58 610 -58 '
                 'C586 -58 582 -27 569 -6 C559 11 548 31 536 60 '
                 'L548 76 C565 52 592 4 610 4'),
        'bars': ('M451 697 L465 711 C500 687 539 680 580 684 '
                 'C633 688 711 700 769 713 C794 719 816 729 824 729 '
                 'C847 729 872 717 872 700 C873 687 863 679 854 674 '
                 'C799 655 672 635 593 634 C532 632 483 651 451 697 Z',
                 'M412 476 L426 490 C475 462 518 450 577 452 '
                 'C646 454 747 472 811 492 C836 500 856 516 866 516 '
                 'C888 516 917 504 917 489 C917 473 909 466 889 458 '
                 'C819 434 683 406 580 406 C509 406 451 427 412 476 Z'),
    },
    True: {
        'width': 104,
        'outer': ((785, 340.5), (782.9, 222), (757, -78), (610, -78)),
        'top': (628, 662), 'upper': ((740, 322), (616, 52)),
        'stem': ('M628 662 L733 676 Q789 496 785 340.5 '
                 'C782.9 222 757 -78 610 -78 '
                 'C580 -78 574 -44 558 -20 C547 -2 534 22 520 54 '
                 'L540 82 C560 54 590 26 610 26'),
        'bars': ('M438 698 L464 724 C516 696 536 702 578 703 '
                 'C630 709 708 720 764 734 C788 740 804 750 824 751 '
                 'C853 751 889 739 893 701 C893 676 878 661 863 654 '
                 'C800 632 676 615 593 615 C526 617 477 630 438 698 Z',
                 'M399 477 L424 503 C490 471 516 469 577 469 '
                 'C643 473 744 489 805 513 C827 520 839 535 866 538 '
                 'C894 536 931 531 938 489 C940 464 919 444 897 437 '
                 'C822 414 686 389 580 389 C503 394 448 405 399 477 Z'),
    },
}


def hooked_wu_stem(bold=False):
    """A compact return with a constant-width approach through the lower bend."""
    master = HOOKED_WU[bold]
    width, outer = master['width'], master['outer']
    top, (control, bottom) = master['top'], master['upper']

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

    # Cut the upper quadratic where it reaches the offset's starting height.
    start, _ = curve(0)
    a = top[1] - 2*control[1] + bottom[1]
    b = 2*(control[1] - top[1])
    cut = (-b - sqrt(b*b - 4*a*(top[1]-start[1])))/(2*a)
    upper_control = tuple(top[j] + cut*(control[j]-top[j]) for j in (0,1))
    upper_end = ((1-cut)**2*top[0] + 2*cut*(1-cut)*control[0] + cut*cut*bottom[0], start[1])
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

    stem = path(master['stem'])
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
    stem.qCurveTo(upper_control, top)
    stem.closePath()
    return stem


def hooked_wu(part, transform, bold=False):
    """One broad outward arc flows through a compact drawn return."""
    upper, lower = HOOKED_WU[bold]['bars']
    return [part('け', [1]), path(upper), path(lower), hooked_wu_stem(bold)]


def reshape(outline, point):
    """Move contour control points without altering the other components."""
    result = RecordingPen()
    result.value = [(op, tuple(None if p is None else point(*p) for p in args))
                    for op, args in outline.value]
    return result


def koto_entry_point(x, y, amount, bar=700):
    """Lower the top bar's entry. Points at or above `bar` belong to the bar."""
    t = max(0, min(1, (610-x)/351))
    return x, y - amount*t*t*(3-2*t) if y >= bar else y


def balanced_koto(parts, bold=False):
    """Accepted E: lower and shift the upper curve, extend the rising stroke."""
    # The heavier Bold bar reaches down to 689; its connector stays below 685.
    bar = 685 if bold else 700
    def smooth(t):
        t = max(0, min(1, t))
        return t*t*(3-2*t)
    def upper(x, y):
        px, py = koto_entry_point(x, y, 44, bar)
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


# NARI's low wave. Each master starts on N's diagonal, runs into E's lower
# return and comes back to N's foot. Bold follows N and E at weight 700.
NARI_WAVE = {
    False: ('M235 198 C272 240 309 266 344 266 C386 266 420 241 465 202 '
            'C521 152 578 33 659 33',
            (((607, -32), (557, 20), (520, 69)),
             ((475, 114), (428, 186), (382, 205)),
             ((350, 220), (308, 223), (280, 204)),
             ((260, 190), (245, 176), (235, 165))),
            ((306, 308), (266, 249), (235, 198))),
    True: ('M250 226 C278 262 300 284 344 285 C395 285 431 254 477 215 '
           'C543 158 580 64 668 64',
           (((590, -43), (548, 16), (507, 58)),
            ((462, 102), (413, 176), (375, 188)),
            ((345, 201), (312, 203), (290, 196)),
            ((282, 193), (276, 191), (271, 189))),
           ((331, 332), (291, 273), (250, 226))),
}


def hiragana_nari(part, bold=False):
    """Native N brush entry, diagonal and foot, joined to NARI's low wave."""
    native = part('ん', [0])
    upper, lower, close = NARI_WAVE[bold]
    outline = path(upper)
    # E's native lower return supplies a full-width rising finish and terminal.
    # Translate it by (-20, -4); its bottom becomes -32, matching N.
    tail = part('え', [0])
    if outline.value[-1][0] == 'endPath':
        outline.value.pop()
    # The return is segment 27 onward in both masters.
    for op,args in tail.value[27:-1]:
        getattr(outline, op)(*((x-20, y-4) for x,y in args))
    for curve in lower:
        outline.curveTo(*curve)
    # Continue the contour through N's foot and upper stroke. Its original
    # high shoulder and lower loop are replaced by the drawn low wave.
    if outline.value[-1][0] == 'endPath':
        outline.value.pop()
    outline.value.extend(native.value[5:17])
    outline.curveTo(*close)
    outline.closePath()
    return [outline]


# MO in TOMO: its top bar and upper stem rise, and its foot drops, by these.
# The foot keeps the spacing of native MO's lower bars.
TOMO_TOP_RISE = 82
TOMO_FOOT_DROP = 12


def tomo_entry_point(x, y):
    t = max(0, min(1, (350-x)/149))
    return x+18*t*t, y-35*t*t


def blend(regular, heavy, t):
    """A drawn stroke between its masters: 0 is Regular, 1 is Bold."""
    numbers = iter(float(v) for v in NUMBER.findall(heavy))
    return NUMBER.sub(lambda m: f'{float(m.group()) + t*(next(numbers) - float(m.group())):.1f}', regular)


NUMBER = re.compile(r'-?\d*\.?\d+')
# Constructions that pack two kana into one cell take lighter strokes in Bold,
# so their verticals keep open gaps. Noto Serif JP's stems at wght 650 are 96
# units wide, 77% of the way from Regular (62) to Bold (106).
DENSE_WEIGHT = 650
DENSE_BLEND = .77


def refinements(part, transform, bold=False, dense_part=None):
    def move(outline, x=0, y=0):
        return transform(outline, (1, 0, 0, 1, x, y))

    def drawn(regular, heavy):
        # Each drawn stroke has a Regular and a Bold master with the same
        # points, drawn to the stroke weights of Noto Serif JP 400 and 700.
        return path(heavy if bold else regular)

    def dense(regular, heavy):
        return path(blend(regular, heavy, DENSE_BLEND) if bold else regular)

    dense_part = dense_part or part

    # One native TO stem, at its original width, shared by TOKI and TOTE.
    stem = move(part('ト', [0]), -220)
    forms = {
        # Curved WU is the default; the hooked form is added as ss01.
        0x1B11F: curved_wu(part, transform, bold),
        # The lower bowl is shallower; the upper connector gains room and
        # a lighter inner curve without changing the top bar's weight.
        0x1B123: [transform(part('と', [0]), (1, 0, 0, .84, 0, -4.32)), drawn(
            'M259 773 L276 794 C313 771 370 753 426 753 '
            'C482 753 546 763 605 774 C634 780 660 790 677 790 '
            'C701 790 738 773 751 752 C762 735 751 720 727 715 '
            'C654 699 601 670 564 636 C522 597 497 550 495 502 '
            'C493 451 513 411 551 383 L506 356 '
            'C467 394 439 443 441 496 C438 561 476 616 537 670 '
            'C556 687 578 710 598 727 C536 716 468 706 418 706 '
            'C350 706 295 738 259 773 Z',
            'M243 772 L273 809 C311 788 368 770 426 770 '
            'C482 770 545 781 602 792 C629 798 653 815 677 815 '
            'C711 814 751 797 771 764 C791 733 763 695 732 691 '
            'C665 671 612 654 575 624 C536 586 518 542 515 501 '
            'C512 450 532 408 570 382 L503 333 '
            'C447 394 419 443 421 496 C418 568 465 627 526 681 '
            'C531 687 537 695 542 701 C500 694 462 689 418 689 '
            'C340 693 295 716 243 772 Z')],

        # A shear makes KI more upright while keeping width at each height.
        # The two crossbars start inside the shared
        # left stem, eliminating an accidental gap or a touching-only join.
        0x1B124: [stem, transform(part('キ', [0]), (1, 0, .075, 1, 60, 0)), drawn(
            'M221 500 C366 526 567 574 700 611 '
            'C739 622 764 634 785 636 C816 639 855 627 863 609 '
            'C871 591 856 581 827 575 C701 552 438 490 222 449 Z',
            'M203.3 514.5 C381 544 553.6 591 694.7 630 '
            'C732.4 640 756.4 652.5 783 655.3 '
            'C819.7 656.3 863 651 880.5 617 '
            'C894 582 860.3 558 830.7 556 '
            'C696.5 533 460 472 210.5 435 Z'), drawn(
            'M222 265 C382 300 611 352 792 402 '
            'C821 410 841 421 863 421 C896 423 933 409 940 393 '
            'C947 374 933 364 906 361 C697 338 450 268 222 211 Z',
            'M204.3 279 C396 319 599.7 362 787 421 '
            'C813.4 428 833.3 439.7 862.4 440.4 '
            'C900.4 440.4 941 432.7 957.4 400 '
            'C970.6 365.4 936 341.6 908 341.7 '
            'C692 323.3 473 252 211 197 Z')],

        # TE keeps the native top bar and descending sweep. The main bar has
        # its own full-width geometry, with a clean join to the same TO stem.
        0x1B125: [stem, move(part('テ', [2]), 80),
                  move(part('テ', [0]), 120), drawn(
            'M221 462 C377 476 624 504 760 519 '
            'C807 524 834 538 850 538 C883 538 925 519 938 501 '
            'C950 483 946 463 926 460 C900 457 867 469 814 468 '
            'C647 468 418 436 222 408 Z',
            'M203 478 C396 493.7 612.5 515.5 758 537.4 '
            'C802.7 544.3 824.4 555.5 850 557.4 '
            'C890.6 556 932.4 539 954.4 512.4 '
            'C976.6 489.7 965.6 444.3 928.6 440.6 '
            'C894 438 865 449.7 814 448.6 '
            'C639 456 440 418.6 209 392.5 Z')],

        # Shortened YO bars, drawn at text weight; RI's left stroke is native
        # size and its right stroke is redrawn with a full-width descending arc.
        0x1B126: [dense(
            'M109 676 L129 684 C150 655 165 633 190 633 '
            'C251 634 369 649 423 657 C442 660 451 674 466 674 '
            'C488 674 542 636 549 617 C554 603 536 591 532 570 '
            'C523 467 513 258 506 108 L447 109 '
            'C452 254 463 477 468 597 C470 607 464 611 453 610 '
            'C373 604 285 591 218 579 C196 575 187 565 174 565 '
            'C149 565 118 608 113 632 Z',
            'M96.6 683.6 L133 697.7 C177 659 174.6 654.6 190 652 '
            'C248 653.7 368 659.3 420 676.6 '
            'C430 675 437.4 691 466 693.3 '
            'C497 690 544 660 560 628 '
            'C567 597 549 584 550 567 '
            'C541.4 456.5 539 278.4 523.4 89.4 L429.4 92.3 '
            'C426 278 444.7 465.3 446 574 '
            'C448 583 442 590 431 590 '
            'C374.7 590.3 287.3 575 221.4 560 '
            'C204.4 558 198.4 547.4 174 546 '
            'C129.7 552 103 594 93 629 Z'), dense(
            'M130 419 L149 430 C173 400 188 381 210 381 '
            'C281 384 383 398 491 407 L488 354 '
            'C380 346 293 333 232 321 C214 317 202 310 188 310 '
            'C163 310 137 351 134 380 Z',
            'M116.3 426 L152 445.4 C201.3 405 196 403 209.6 400.5 '
            'C287.7 402.5 361.5 417 505.4 422 L505 337.4 '
            'C362 329.3 305.3 313.6 236 302 '
            'C221 299 209 291 188 290.5 C142.3 295 121 341 113 378 '
            'Z'), dense(
            'M98 166 L116 177 C141 145 157 126 182 126 '
            'C251 128 384 147 455 152 C484 154 518 138 523 120 '
            'C528 103 516 87 495 87 C475 87 451 95 420 95 '
            'C342 92 263 79 213 68 C194 64 182 56 168 56 '
            'C142 56 108 99 104 126 Z',
            'M84.6 172 L118.6 191 '
            'C168 149.5 164.6 149.4 181.7 145.6 '
            'C248 146.5 382 162.6 453.6 171.6 '
            'C490 172 528.4 160.3 543 125.7 '
            'C553 95.7 526 65.5 495 67.3 C470 68 447 75 420.4 76 '
            'C344.3 77.7 266 59.7 217 49 C201.7 46 190 37 168 36.4 '
            'C123.3 41 91.6 85.3 84 123 Z'),
            move(dense_part('リ', [1]), 333), dense(
            'M754 731 C779 740 803 748 825 748 '
            'C849 748 902 725 923 702 C944 681 919 668 915 633 '
            'C912 571 914 474 909 402 C904 234 831 83 669 -48 '
            'L650 -30 C780 111 835 248 840 406 '
            'C843 484 846 585 844 653 C843 677 835 691 819 697 '
            'C802 705 778 708 754 712 Z',
            'M743 738.7 C783 758.3 793.3 766 825 768.7 '
            'C860 771 912.5 749 941 719 '
            'C975.5 676 937 646.6 939.6 631 '
            'C933.7 572.6 938.5 473 932.3 401 '
            'C924 224 857 73.6 668.4 -62 L635 -30.5 '
            'C770.6 135 806.4 249 816.7 407 '
            'C818.7 484.7 824 585.7 819 652 '
            'C817 672.7 815.7 669 810 676 '
            'C792.6 686 787 691 743.7 703.3 Z')],

        # NE's upper turn and return are drawn as kana strokes. The crossbar
        # comes from native WI, with its brush entry and rising line intact.
        0x1B127: [drawn(
            'M223 710 L240 722 C258 699 274 682 303 683 '
            'C406 691 577 709 689 723 C710 727 721 742 735 742 '
            'C752 742 787 721 796 708 C805 694 790 685 774 674 '
            'C708 621 626 560 533 509 L513 531 '
            'C585 583 651 641 696 695 C586 676 449 652 329 631 '
            'C308 627 294 615 280 615 C261 631 237 654 229 672 Z',
            'M209 716 L242.3 738 '
            'C284.5 700.3 281.3 712 301.7 705.5 '
            'C402 714 579 706.7 685.3 746.6 '
            'C695 748 703 762.4 735 766.7 '
            'C768 763 798 745.7 815 720.7 '
            'C832.6 683 799.4 660 789 654 '
            'C718.5 599.4 644 552.3 530.5 494 L495.5 533 '
            'C574 579.6 661 703 653 670.3 '
            'C645 680 423.7 629.4 333 609.4 '
            'C313.4 606.4 317 595 272 592.5 '
            'C237 623 224.5 631.4 211 666.7 Z'), drawn(
            'M483 526 C495 541 518 547 537 551 L550 522 '
            'C543 496 542 472 542 447 L542 76 '
            'C542 15 531 -14 510 -29 C492 -42 476 -45 457 -40 '
            'C443 -35 439 -25 428 -16 C406 6 372 25 331 44 L342 64 '
            'C385 43 421 30 457 25 C477 23 483 36 483 57 '
            'C484 163 484 295 483 429 C483 469 483 496 483 526 Z',
            'M460.7 534 C501.7 572 488.7 562 549 575 L573.6 524 '
            'C563 483.4 565.5 476 563.6 447 L563.6 76 '
            'C564.6 13.7 554.6 -25.6 523.5 -48 '
            'C501.7 -64 476.6 -70 450 -62 '
            'C424.3 -52 421 -39 412.5 -33 '
            'C392 -5.5 380 14 319.3 40 L338.5 75 '
            'C396.4 43.5 423.6 51 460 48 '
            'C463.7 50.6 454.7 37 461 57 '
            'C463 163 462 295 461.4 429 '
            'C461.3 474 460 486 460.7 534 Z'),
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
        0x2A708: [stem, move(reshape(part('モ', [2]), tomo_entry_point), 90, TOMO_TOP_RISE),
                  reshape(part('モ', [0]), lambda x, y:
                          (x+90, y-TOMO_FOOT_DROP+(TOMO_TOP_RISE+TOMO_FOOT_DROP)*max(0, min(1, (y-180)/310)))), drawn(
            'M220 390 C410 405 649 435 791 454 '
            'C822 458 839 467 855 466 C885 465 928 445 938 426 '
            'C949 406 935 391 915 391 C881 391 854 399 821 399 '
            'C636 396 403 360 220 336 Z',
            'M202.3 406.4 C429 421.5 637.4 446.6 788.4 473.5 '
            'C816.6 477 832 486 856 485.7 C893 483 936 466 956 436 '
            'C976.3 403 944 367.7 915 371.3 '
            'C878 371.5 850.3 379.5 821 379.3 '
            'C629 385 424 341.5 207 321.3 Z')],

        # Retain SHI’s enlarged dot length, with 104% transverse weight to match NO.
        0x2CF00: [transform(part('ノ'), (1, 0, .12, 1.06, 3, 0)),
                  transform(part('シ', [1]), (1.12, -.04, -.04, 1.06, 194.54, 49.08))],

        # Keep a substantial entry and neck, with a lighter bowl and a shoulder
        # moved inward to balance the long lower sweep. SHI is unchanged.
        0x2CEFF: [move(part('シ', [2]), -51, -14), drawn(
            'M155 384 L161 424 C193 442 235 453 266 442 '
            'C306 428 324 390 346 347 C385 269 425 202 490 162 '
            'C554 124 627 105 715 105 C772 105 822 112 865 122 '
            'C889 129 911 117 918 101 C925 84 913 71 893 65 '
            'C840 50 780 42 715 42 C607 42 519 60 452 101 '
            'C372 150 334 229 308 300 C288 354 281 380 257 391 '
            'C232 402 193 383 155 384 Z',
            'M140 371.6 L145 435 C196 466 228 470.6 272.3 460 '
            'C321.4 441.4 339 396.7 364 356 '
            'C406.4 280.3 444 217.6 502.3 182.3 '
            'C562 147 630 127.6 715 127.3 '
            'C770 127.3 819 134 859.4 143.5 '
            'C892.6 152.6 926 137.4 938 109.6 '
            'C952 76.3 924 49 899 43.7 C843.6 28 782 19.6 715 19.7 '
            'C604.7 19.4 512 36.4 439.6 81 '
            'C352.6 134.4 312 219.6 288 292.6 '
            'C270.5 349 263.5 370.6 249 373.7 '
            'C230.5 383.6 216 360 140 371.6 Z')],

        # NARI retains the Japanese chart's long diagonal. N's brush entry
        # and rounded foot supply its Mincho weight variation.
        0x2CF02: hiragana_nari(part, bold),
    }
    # TOMO, TOTE and TOKI share one TO stem and an optical size around the
    # (500, 365) centre; TOKI's crossing strokes take it to 90%, like TOMO.
    # Each moves right so the shared stem lines up and the ink, which lies
    # mostly right of that stem, centres in the cell. YORI carries two kana in
    # one cell: its reduction brings its blackness near the densest native
    # kana, and it moves left, since RI's two strokes weight its right side.
    # Bold YORI draws lighter strokes (DENSE_WEIGHT) at 95%, so its strokes
    # match the kana around it while its verticals stay apart.
    yori = (.95, -50) if bold else (.90, -45)
    for cp, scale, shift in ((0x2A708, .90, 25), (0x1B125, .92, 35), (0x1B124, .90, 25), (0x1B126, *yori)):
        forms[cp] = [transform(p, (scale, 0, 0, scale,
                                  500*(1-scale) + shift, 365*(1-scale))) for p in forms[cp]]
    forms[0x1B123] = balanced_koto(forms[0x1B123], bold)
    return forms


DESCRIPTIONS = {
    0x1B11F: 'Curved WU preserves the native KE descent. Stylistic set 1 keeps the upper outward bow and carries its weight through a compact rounded return, set farther right.',
    0x1B123: 'KOTO E: a lower upper curve shifted left, with a longer rising right stroke and a shallow Noto TO bowl.',
    0x1B124: 'Noto TO stem and an upright KI diagonal with joined crossbars, at 90% optical size like TOMO. The shared TO stem aligns with TOMO and TOTE, and the ink centres in the cell.',
    0x1B125: 'Noto Serif JP TO stem and TE strokes with a drawn connecting bar, at 92% optical size. The shared TO stem aligns with TOMO and TOKI, and the ink centres in the cell.',
    0x1B126: 'Noto Serif JP RI short stroke; redrawn YO bars and an RI descending stroke of full width, at 90% optical size and centred in the cell. Bold draws its strokes at the weight of Noto Serif JP 650 and at 95%, keeping the three verticals apart.',
    0x1B127: 'A modulated upper bar and lighter return above a hooked stem. The middle crossbar sits halfway between its 0.107 and 0.108 positions.',
    0x1B128: 'Noto WI bars join a NA-derived left descent and the native right stem. Stem spacing is halfway between 0.107 and 0.108; stroke weights are preserved.',
    0x2A708: 'Native MO stem and return beside TO. MO’s upturned entry is lower and shorter, giving the nearby TO head more space, and its lower return keeps the spacing of native MO. At 90% optical size, with the shared TO stem aligned with TOTE and TOKI.',
    0x2CF00: 'An enlarged SHI dot meets the NO-derived descent directly. Its transverse weight is closer to NO while its length is unchanged.',
    0x2CEFF: 'Native SHI upper stroke with a substantial lower entry and neck. The shoulder sits farther inward and the bowl has less weight.',
    0x2CF02: 'Redrawn NARI retains its upper stroke and rounded foot. The lower wave has steadier weight and Noto E’s full, rounded finish.',
}
