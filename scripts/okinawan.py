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


def add_okinawan(font, add, make_glyph, contours, transform, add_feature):
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
    ku_head = path('M551 796 L570 801 Q662 759 675 713 Q681 696 654 678 '
        'Q479 575 318 494 Q292 480 316 468 L604 351 L577 297 '
        'Q423 381 281 444 Q223 472 272 511 Q404 606 548 706 '
        'Q588 738 551 796 Z')
    joined_i = path('M565 361 L613 340 Q582 247 604 120 Q611 69 634 70 '
        'L677 167 L697 155 L661 49 Q654 8 622 13 Q549 38 547 162 '
        'Q546 255 565 361 Z')
    ti_head = path('M76 618 L95 624 Q131 574 158 574 '
        'Q191 574 568 670 Q731 712 795 711 Q878 710 896 665 '
        'Q898 638 862 639 Q703 655 608 605 '
        'C505 536 454 386 463 285 C466 215 505 172 565 157 '
        'L560 126 Q471 130 429 202 Q389 273 412 390 '
        'Q440 532 551 621 Q422 594 237 519 Q194 494 176 494 '
        'Q115 502 80 572 Z')
    ti_hook = path('M532 182 L584 171 Q560 98 594 50 '
        'Q607 30 621 50 L654 115 L673 106 L643 23 '
        'Q635 -6 611 -4 Q531 17 532 182 Z')
    wa_tail = [part('わ', [0], (.55, 0, 0, .62, 300, -30)),
               path('M540 362 Q576 337 575 296 L574 -39 L530 -55 '
                    'L530 289 Q531 327 520 346 Z'),
               path('M545 297 Q432 218 430 135 Q429 68 529 97 L539 135 '
                    'Q479 93 462 133 Q451 179 555 255 Z')]
    e_tail = part('え', [0], (.56, 0, 0, .57, 325, -28))
    joined_e = path('M604 351 L642 322 Q621 293 596 271 L496 166 '
        'Q540 183 570 150 Q589 126 600 74 Q609 43 641 39 '
        'Q692 34 766 55 Q797 63 813 43 Q826 25 801 12 '
        'Q734 -19 665 -16 Q582 -18 563 35 Q551 67 546 103 '
        'Q540 130 520 133 Q491 139 461 110 L406 40 '
        'Q382 10 361 11 Q340 17 355 41 L574 313 Z')
    tsi_hook = path('M299 260 L349 259 Q332 129 365 47 '
        'Q378 20 398 46 L433 111 L454 98 L418 15 '
        'Q407 -13 382 -5 Q299 17 290 128 Q285 198 299 260 Z')
    # TU and WU share the descending return of the ligature's small U.
    u_return = path('M548 175 Q747 189 787 89 Q813 6 662 -49 '
                    'L637 -29 Q751 26 716 80 Q691 132 546 124 Z')
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
                  path('M279 597 Q367 617 470 625 Q538 641 542 602 '
                       'Q541 580 521 543 Q469 432 397 278 Q331 127 249 27 '
                       'Q210 -20 165 14 Q107 75 173 178 Q256 302 457 372 '
                       'L447 337 Q287 268 216 163 Q165 78 197 63 Q225 42 275 134 '
                       'Q385 331 460 559 Q363 537 327 547 Q297 561 279 597 Z')],
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
