"""Keep the released repertoire intact while appending new forms."""
import hashlib
import copy
from fontTools.ttLib import TTFont
from PIL import ImageChops
from check_refinements import mask
from honkoku import HONKOKU, TALLIES
from okinawan import PUA as OKINAWAN_PUA
from sources import ROOT


def check_iteration(path, font):
    baseline = ROOT/'releases/v0.112/GenZuiSerif-Regular.ttf'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == '66da0b1d794412593fcd62bcbb977085cf8db843b77b2ec199f1d3495ba2621c'
    before = TTFont(baseline)
    cmap, old_cmap = font.getBestCmap(), before.getBestCmap()
    assert set(cmap)-set(old_cmap) == set(HONKOKU) | set(OKINAWAN_PUA)
    assert all(cmap[cp] == name for cp, name in old_cmap.items())
    old_order = before.getGlyphOrder()
    assert font.getGlyphOrder()[:len(old_order)] == old_order
    assert len(font.getGlyphOrder()) == len(old_order)+len(HONKOKU)+len(OKINAWAN_PUA)+7
    for name in old_order:
        assert before['glyf'][name].getCoordinates(before['glyf']) == font['glyf'][name].getCoordinates(font['glyf']), name
        for table in ('hmtx', 'vmtx'):
            assert font[table][name] == before[table][name], (table, name)
    # Appending symbols must leave every previous layout rule and IVS intact.
    for table in ('GPOS', 'BASE'):
        assert font[table].compile(font) == before[table].compile(before), table
    # Okinawan voicing appends exactly one ccmp lookup. Removing only that
    # addition must recover the released table byte for byte.
    gsub = copy.deepcopy(font['GSUB'])
    table = gsub.table
    old_count = before['GSUB'].table.LookupList.LookupCount
    assert table.LookupList.LookupCount == old_count + 1
    table.LookupList.Lookup.pop()
    table.LookupList.LookupCount = old_count
    for record in table.FeatureList.FeatureRecord:
        indices = record.Feature.LookupListIndex
        if old_count in indices:
            assert record.FeatureTag == 'ccmp'
            indices.remove(old_count)
            record.Feature.LookupCount = len(indices)
    assert gsub.compile(font) == before['GSUB'].compile(before), 'previous GSUB rules'
    assert [t.uvsDict for t in font['cmap'].tables if t.format == 14] == [
        t.uvsDict for t in before['cmap'].tables if t.format == 14]
    for cp in HONKOKU:
        name = cmap[cp]
        glyph = font['glyf'][name]
        assert glyph.numberOfContours > 0
        assert 0 <= glyph.xMin < glyph.xMax <= 1000
        assert -120 <= glyph.yMin < glyph.yMax <= 880
        assert font['hmtx'][name] == (1000, glyph.xMin)
        assert font['vmtx'][name] == (1000, 880-glyph.yMax)
    # A tally adds ink in the same cell; the fifth mark reads as native 正.
    tally_checks = []
    for size in (24, 48, 128, 1000):
        rasters = [mask(path, cp, size) for cp in TALLIES]
        areas = [sum(im.getdata()) for im in rasters]
        assert all(a < b for a, b in zip(areas, areas[1:])), (size, areas)
        # Auto-hinting may move strokes when another stem is introduced.
        # At one pixel per font unit the added strokes must lose no ink.
        if size == 1000:
            for previous, current in zip(rasters, rasters[1:]):
                assert ImageChops.subtract(previous, current).getbbox() is None, size
        native = mask(path, 0x6B63, size)
        assert ImageChops.difference(native, rasters[-1]).getbbox() is None, size
        tally_checks.append({'size_px':size, 'increasing_ink_area':True, 'fifth_matches_native_zheng':True})
    before.close()
    return {'baseline':'0.112', 'changed_outlines':[],
            'unchanged_glyphs':len(old_order),
            'added_codepoints':[f'U+{cp:X}' for cp in sorted(set(HONKOKU) | set(OKINAWAN_PUA))],
            'all_previous_outlines_and_metrics_unchanged':True,
            'previous_layout_rules_and_ivs_unchanged':True,
            'fullwidth_advances_and_vertical_origins_verified':True,
            'tally_checks':tally_checks, 'status':'passed'}
