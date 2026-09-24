"""Funatsu kana and prefectural raised katakana, drawn from Noto components.

Mapping references describe character identity, not an upstream outline licence.
No outlines are imported from Nishiki-teki, Xim Sans or legacy Okinawan fonts.
"""
import json
import pathops
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib.tables import otTables
from fontTools.otlLib.builder import buildLigatureSubstSubtable
from serif_forms import path
from sources import ROOT

DATA = json.loads((ROOT/'data/okinawan/mappings.json').read_text())
ENTRIES = DATA['characters']
PUA = {int(e['output'][0], 16): e for e in ENTRIES
       if len(e['output']) == 1 and 0xE000 <= int(e['output'][0], 16) <= 0xF8FF}
DESCRIPTIONS = {cp: (f"{e['label']}. " +
    ('Funatsu New Okinawan Kana; Nishiki-teki PUA convention. ' if e['system'] == 'funatsu' else
     'Okinawa prefectural raised katakana; Xim Sans PUA convention. ') +
    'GenZui drawing from Noto components. This is a private-use mapping, not a Unicode assignment.')
    for cp, e in PUA.items()}


def add_okinawan(font, add, make_glyph, contours, transform, add_feature,
                  bold=False):
    def drawn(regular, heavy):
        # Regular and Bold masters of one drawn stroke, with the same points.
        return path(heavy if bold else regular)

    def unite(parts):
        # Union independently filled components: opposite native/custom winding
        # must not punch holes into a shared join.
        merged = pathops.Path()
        for part in parts:
            shape = pathops.Path()
            part.replay(shape.getPen())
            merged = pathops.op(merged, shape, pathops.PathOp.UNION)
        pen = RecordingPen()
        merged.draw(pen)
        return make_glyph([pen])

    def part(ch, indices=None, matrix=None):
        pen = contours(font, ord(ch), indices)
        return transform(pen, matrix) if matrix else pen

    fu_left = contours(font, ord('ふ'), [1])
    native = pathops.Path()
    fu_left.replay(native.getPen())
    clip = pathops.Path()
    path('M0 -200 H620 V900 H0 Z').replay(clip.getPen())
    fu_left = RecordingPen()
    pathops.op(native, clip, pathops.PathOp.INTERSECTION).draw(fu_left)

    def fu(matrix):
        return [part('ふ', [0], matrix), transform(fu_left, matrix)]

    # Ligature strokes occupy one kana cell. Their joined descents and added
    # onset strokes follow Funatsu's 2016 chart and the 2023 proposal chart.
    i_tail = [part('い', [0], (.5, 0, 0, .48, 330, -55)),
              part('い', [1], (.5, 0, 0, .48, 370, -45))]
    ku_head = drawn(
                  'M551 796 L570 801 Q662 759 675 713 Q681 696 654 678 '
                  'Q479 575 318 494 Q292 480 316 468 L604 351 L577 297 '
                  'Q423 381 281 444 Q223 472 272 511 Q404 606 548 706 '
                  'Q588 738 551 796 Z',
                  'M536 802 L571 815.3 Q684 788.3 699 720.7 '
                  'Q705.7 678 667.6 656.4 Q490.6 552 325.4 479.7 '
                  'Q321 477.6 323 483.3 L625.3 359 L584.4 273.5 '
                  'Q405 374 273 426 Q197 468.4 260 526.7 '
                  'Q393 623.3 533 726 Q553.4 724 536 802 Z')
    joined_i = drawn(
                   'M565 361 L613 340 Q582 247 604 120 Q611 69 634 70 '
                   'L677 167 L697 155 L661 49 Q654 8 622 13 '
                   'Q549 38 547 162 Q546 255 565 361 Z',
                   'M555.6 378.6 L635 350 Q595.5 235.7 623.3 123 '
                   'Q645.4 79.4 620 90.4 L672.7 180.5 L708.3 159 '
                   'L681.4 44 Q674 -9.5 617 -7.5 Q526 30.3 527.6 161.7 '
                   'Q524 246 555.6 378.6 Z')
    ti_head = drawn(
                  'M76 618 L95 624 Q131 574 158 574 Q191 574 568 670 '
                  'Q731 712 795 711 Q878 710 896 665 Q898 638 862 639 '
                  'Q703 655 608 605 C505 536 454 386 463 285 '
                  'C466 215 505 172 565 157 L560 126 Q471 130 429 202 '
                  'Q389 273 412 390 Q440 532 551 621 Q422 594 237 519 '
                  'Q194 494 176 494 Q115 502 80 572 Z',
                  'M63 626.7 L100 639 Q157.7 588 158 598.5 '
                  'Q184 590.3 562 693.3 Q725.7 733.5 795.3 734.3 '
                  'Q887 738 916.5 669.7 Q914 614.4 860.6 616.5 '
                  'Q703 631 620.3 584.3 C522.4 531 477 377.3 484.6 286.4 '
                  'C494 221.3 500 195 579.5 166.5 L571 113 '
                  'Q454 111 411.6 192 Q365.4 272 391 394 '
                  'Q444 570 507.5 600.4 Q460 582.7 247.7 497 '
                  'Q209 472 174.4 469.5 Q95 478.7 61 566.7 Z')
    ti_hook = drawn(
                  'M532 182 L584 171 Q560 98 594 50 Q607 30 621 50 '
                  'L654 115 L673 106 L643 23 Q635 -6 611 -4 '
                  'Q531 17 532 182 Z',
                  'M519.7 197.3 L603.5 182 Q573 86.6 606 58 '
                  'Q608.7 53 607 58.5 L650 126.5 L684 110.5 L658.7 18 '
                  'Q649.6 -20 608 -20 Q511.4 2.5 519.7 197.3 Z')
    wa_tail = [part('わ', [0], (.55, 0, 0, .62, 300, -30)),
               drawn(
                   'M540 362 Q576 337 575 296 L574 -39 L530 -55 L530 289 '
                   'Q531 327 520 346 Z',
                   'M539.4 378.5 Q599 343 591.6 296 L590.5 -50.6 L520 -69 '
                   'L513.4 289 Q517 317 502 349.4 Z'),
               drawn(
                   'M545 297 Q432 218 430 135 Q429 68 529 97 L539 135 '
                   'Q479 93 462 133 Q451 179 555 255 Z',
                   'M551.7 314.7 Q410 223.4 417 135 Q420 49 537 89 '
                   'L545 143.4 Q468.4 109 474.4 137 '
                   'Q455.7 162.3 571.6 249 Z')]
    e_tail = part('え', [0], (.56, 0, 0, .57, 325, -28))
    joined_e = drawn(
                   'M604 351 L642 322 Q621 293 596 271 L496 166 '
                   'Q540 183 570 150 Q589 126 600 74 Q609 43 641 39 '
                   'Q692 34 766 55 Q797 63 813 43 Q826 25 801 12 '
                   'Q734 -19 665 -16 Q582 -18 563 35 Q551 67 546 103 '
                   'Q540 130 520 133 Q491 139 461 110 L406 40 '
                   'Q382 10 361 11 Q340 17 355 41 L574 313 Z',
                   'M601 375 L665 325.4 Q627 271 607.7 259 L526 186 '
                   'Q517 196.4 582 160 Q606 131 618 78.5 Q625 61 643 59 '
                   'Q688 54.5 760.7 74.6 Q802 85 828 54.4 '
                   'Q848 15.6 809.6 -5.6 Q738 -40 665 -36 '
                   'Q573 -40 544.7 28.3 Q534 63.3 528.7 100 '
                   'Q526 118 517.3 118 Q499.5 117.6 473 99.4 L417.6 31 '
                   'Q393.5 -3.4 359 -2.7 Q321.3 14 343 49.6 L560.5 324 Z')
    tsi_hook = drawn(
                   'M299 260 L349 259 Q332 129 365 47 Q378 20 398 46 '
                   'L433 111 L454 98 L418 15 Q407 -13 382 -5 '
                   'Q299 17 290 128 Q285 198 299 260 Z',
                   'M292 262 L364 261 Q352 116 380 50 '
                   'Q390 32 404 56 L431 124 L467 102 L432 9 '
                   'Q417 -29 378 -20 Q281 4 270 127 Q264 190 292 262 Z')
    # TU and WU share the descending return of the ligature's small U.
    u_return = drawn(
                   'M548 175 Q747 189 787 89 Q813 6 662 -49 L637 -29 '
                   'Q751 26 716 80 Q691 132 546 124 Z',
                   'M530 192.5 Q764.4 217 809 97 Q838 -18.5 660 -62.4 '
                   'L619 -27 Q739 53.4 696 68.6 Q702.3 105.6 529.5 107 Z')
    recipes = {
        0xF450: [part('と', [1], (.92, 0, 0, .84, 0, 115)),
                  part('と', [0], (.88, 0, 0, .72, -5, 185)), u_return],
        0xF452: [ti_head, ti_hook, part('い', [1], (.43, 0, 0, .44, 475, -38))],
        0xF454: [ku_head, *wa_tail],
        0xF456: [ku_head, joined_i, part('い', [1], (.43, 0, 0, .48, 460, -42))],
        0xF458: [ku_head, joined_e],
        0xF45A: [*fu((.72, 0, 0, .88, -5, 80)), *[
            transform(p, (.72, 0, 0, .75, 268, 0)) for p in wa_tail]],
        0xF45B: [*fu((.69, 0, 0, .94, 0, 45)), *[
            transform(p, (.72, 0, 0, 1, 280, 0)) for p in i_tail]],
        0xF45C: [*fu((.69, 0, 0, .94, 0, 45)),
                  transform(e_tail, (.76, 0, 0, 1.05, 240, 0))],
        0xF45D: [part('や', matrix=(.88, 0, 0, .91, 65, 20)),
                  part('い', [0], (.26, 0, 0, .48, 82, 276))],
        0xF45E: [part('ゆ', matrix=(.84, 0, 0, .94, 116, 0)),
                  part('い', [0], (.25, 0, 0, .85, 30, 35))],
        0xF45F: [part('よ'), part('い', [0], (.28, 0, 0, .51, 152, 351))],
        0xF460: [part('う', [1], (.76, 0, 0, .65, 63, 294)),
                  part('わ', [0], (.94, 0, 0, .96, -34, -5)),
                  drawn(
                      'M279 597 Q367 617 470 625 Q538 641 542 602 '
                      'Q541 580 521 543 Q469 432 397 278 Q331 127 249 27 '
                      'Q210 -20 165 14 Q107 75 173 178 Q256 302 457 372 '
                      'L447 337 Q287 268 216 163 Q165 78 197 63 '
                      'Q225 42 275 134 Q385 331 460 559 Q363 537 327 547 '
                      'Q297 561 279 597 Z',
                      'M263 604.5 Q373 650 466 649.6 Q543.7 674.6 567 602.7 '
                      'Q564 568 543 532 Q483.3 425.7 416.7 269 '
                      'Q338.6 123 264.6 14 Q216 -48 150.5 -2 '
                      'Q84.7 80 159 187 Q237 321.5 466 381.4 L464 322 '
                      'Q289 252.4 229.6 154.3 Q188.7 68.3 208 81.6 '
                      'Q203 58.3 261.5 141.4 Q378.5 369 423 525.5 '
                      'Q400 520.4 319 525.3 Q277 534.3 263 604.5 Z')],
        0xF461: [part('ゐ', matrix=(.94, 0, 0, .79, 22, -4)),
                  part('う', [1], (.73, 0, 0, .65, 77, 289))],
        0xF462: [part('ゑ', matrix=(.94, 0, 0, .79, 22, -4)),
                  part('う', [1], (.73, 0, 0, .65, 77, 289))],
        0xF463: [part('ん'), part('い', [1], (.29, 0, 0, .37, 452, 389))],
        0xF465: [part('を', matrix=(.94, 0, 0, .77, -16, 182)), u_return],
        0xF467: [part('す', matrix=(.8, 0, 0, 1, 0, 0)),
                  part('い', [1], (.65, 0, 0, .78, 249, -100))],
        0xF469: [part('つ', matrix=(.92, 0, 0, .91, 0, 160)), tsi_hook, part('い', [1], (.43, 0, 0, .48, 370, -42))],
    }
    for cp, entry in PUA.items():
        if entry['system'] == 'prefecture':
            # Half-em advance, raised into the upper half of a full kana cell.
            recipes[cp] = [part(chr(int(entry['base'], 16)), matrix=(.48, 0, 0, .48, 10, 410))]
    for cp, parts in recipes.items():
        name = add(font, f'okinawa.u{cp:04X}', unite(parts))
        g = font['glyf'][name]
        raised = PUA[cp]['system'] == 'prefecture'
        font['hmtx'][name] = (500 if raised else 1000, g.xMin)
        font['vmtx'][name] = (500 if raised else 1000, 880-g.yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format in (4, 12):
                table.cmap[cp] = name
    # Use a composition lookup so combining dakuten works even when a shaping
    # engine assigns an unknown script to the private-use base. The text stays
    # base + U+3099; the composed drawings are unencoded glyphs.
    mapping = {}
    cmap = font.getBestCmap()
    for e in ENTRIES:
        if len(e['output']) != 2 or int(e['output'][0], 16) not in PUA:
            continue
        cp = int(e['output'][0], 16)

        original_mark = font['glyf'][cmap[0x309B]]
        mark = part('゛', matrix=(.72, 0, 0, .72, 810-.72*original_mark.xMin, 825-.72*original_mark.yMax))
        name = add(font, f"okinawa.{e['id']}", unite([
            transform(p, (.9, 0, 0, .9, 0, 0)) for p in recipes[cp]]+[mark]))
        font['vmtx'][name] = (1000, 880-font['glyf'][name].yMax)
        font['GDEF'].table.GlyphClassDef.classDefs[name] = 1
        mapping[(cmap[cp], cmap[0x3099])] = name
    lookup = otTables.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable = [buildLigatureSubstSubtable(mapping)]
    lookup.SubTableCount = 1
    add_feature(font, 'GSUB', 'ccmp', lookup)
