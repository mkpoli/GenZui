"""Build GenZui Sans P: GenZui Sans with its own GPOS palt widths baked in."""
import json
from collections import Counter

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import ValueRecord

from sans import BOLD_STEM, FAMILY, FAMILY_JA, OUT, STEM, VERSION

FAMILY_P = FAMILY + ' P'
FAMILY_P_JA = FAMILY_JA + 'P'
STEM_P = 'GenZuiSansP-Regular'
BOLD_STEM_P = 'GenZuiSansP-Bold'
PACKAGE_P = f'GenZuiSansP-{VERSION}.zip'
DESCRIPTION = ('GenZui Sans with the proportional kana and punctuation widths of its palt feature '
               'applied by default.')
# Script and language systems Japanese text selects. HarfBuzz shapes Hiragana
# through kana and Kanji through hani; Word and DirectWrite use the same tags.
JAPANESE = (('DFLT', None), ('kana', None), ('kana', 'JAN '), ('hani', None), ('hani', 'JAN '),
            ('latn', None), ('latn', 'JAN '))


def subtables(lookup):
    """(lookup type, subtable) pairs, with extension subtables unwrapped."""
    for sub in lookup.SubTable:
        if lookup.LookupType == 9:
            yield sub.ExtensionLookupType, sub.ExtSubTable
        else:
            yield lookup.LookupType, sub


def feature_lookups(gpos, script, language, tag):
    """Lookup indexes the tag reaches through one script and language system, or None if it has no such system."""
    for record in gpos.ScriptList.ScriptRecord:
        if record.ScriptTag != script:
            continue
        if language is None:
            system = record.Script.DefaultLangSys
        else:
            found = [r.LangSys for r in record.Script.LangSysRecord if r.LangSysTag == language]
            system = found[0] if found else None
        if system is None:
            return None
        return sorted({i for index in system.FeatureIndex if gpos.FeatureList.FeatureRecord[index].FeatureTag == tag
                       for i in gpos.FeatureList.FeatureRecord[index].Feature.LookupListIndex})
    return None


def single_adjustments(lookup, tally):
    """Glyph name to ValueRecord for one SinglePos lookup. The first subtable covering a glyph wins."""
    result = {}
    for kind, sub in subtables(lookup):
        assert kind == 1, 'palt references a lookup that is not single adjustment'
        tally['SinglePos format %d' % sub.Format] += 1
        assert not sub.ValueFormat & 0xF0, 'device tables in palt'
        for position, name in enumerate(sub.Coverage.glyphs):
            value = sub.Value if sub.Format == 1 else sub.Value[position]
            result.setdefault(name, value)
    return result


def palt_adjustments(font):
    """Per glyph (XPlacement, XAdvance) from the lookups palt reaches under Japanese script and language systems."""
    gpos = font['GPOS'].table
    reached = {}
    for script, language in JAPANESE:
        lookups = feature_lookups(gpos, script, language, 'palt')
        if lookups is not None:
            reached[f'{script}/{language or "default"}'] = lookups
    assert len({tuple(v) for v in reached.values()}) == 1, reached
    indexes = next(iter(reached.values()))
    tally, adjustments = Counter(), Counter()
    total = {}
    for index in indexes:
        lookup = gpos.LookupList.Lookup[index]
        assert lookup.LookupType == 1 and not lookup.LookupFlag, index
        for name, value in single_adjustments(lookup, tally).items():
            assert not getattr(value, 'YPlacement', 0) and not getattr(value, 'YAdvance', 0), name
            dx, da = getattr(value, 'XPlacement', 0) or 0, getattr(value, 'XAdvance', 0) or 0
            previous = total.get(name, (0, 0))
            total[name] = (previous[0]+dx, previous[1]+da)
    total = {name: pair for name, pair in total.items() if pair != (0, 0)}
    return total, {'reached_through': reached, 'lookups': indexes, 'subtables': dict(tally)}


def shift(font, deltas):
    """Move each glyph's outline by its XPlacement and widen it by its XAdvance."""
    glyf, hmtx = font['glyf'], font['hmtx']
    order = font.getGlyphOrder()
    # A composite's components are offset by the difference between its own shift and its component's.
    for name in order:
        glyph = glyf[name]
        if not glyph.isComposite():
            continue
        own = deltas.get(name, (0, 0))[0]
        for component in glyph.components:
            change = own - deltas.get(component.glyphName, (0, 0))[0]
            if not change:
                continue
            assert component.flags & 0x2 and not hasattr(component, 'transform'), name
            component.x += change
    for name in order:
        glyph = glyf[name]
        if name in deltas and not glyph.isComposite() and glyph.numberOfContours:
            glyph.coordinates.translate((deltas[name][0], 0))
    for _ in range(4):  # composites need their components' bounds first
        for name in order:
            if glyf[name].numberOfContours:
                glyf[name].recalcBounds(glyf)
    for name, (dx, da) in deltas.items():
        advance, _ = hmtx[name]
        glyph = glyf[name]
        hmtx[name] = (advance+da, glyph.xMin if glyph.numberOfContours else 0)


def shift_anchors(gpos, deltas):
    """Mark attachment anchors follow the outlines that carry them."""
    moved = 0

    def move(anchor, name):
        nonlocal moved
        if anchor is not None and deltas.get(name, (0, 0))[0]:
            anchor.XCoordinate += deltas[name][0]
            moved += 1

    for lookup in gpos.LookupList.Lookup:
        for kind, sub in subtables(lookup):
            assert kind in (1, 2, 4, 5, 6), f'GPOS lookup type {kind} is not handled'
            if kind == 4:
                for name, record in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
                    move(record.MarkAnchor, name)
                for name, record in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
                    for anchor in record.BaseAnchor:
                        move(anchor, name)
            elif kind == 5:
                for name, record in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
                    move(record.MarkAnchor, name)
                for name, attach in zip(sub.LigatureCoverage.glyphs, sub.LigatureArray.LigatureAttach):
                    for component in attach.ComponentRecord:
                        for anchor in component.LigatureAnchor:
                            move(anchor, name)
            elif kind == 6:
                for name, record in zip(sub.Mark1Coverage.glyphs, sub.Mark1Array.MarkRecord):
                    move(record.MarkAnchor, name)
                for name, record in zip(sub.Mark2Coverage.glyphs, sub.Mark2Array.Mark2Record):
                    for anchor in record.Mark2Anchor:
                        move(anchor, name)
    return moved


def vertical_compensation(font, original, deltas):
    """Per glyph XPlacement that puts vertical ink where GenZui Sans has it.

    HarfBuzz places a vertical glyph's origin at half the horizontal advance, rounded down.
    """
    result = {}
    for name, (dx, da) in deltas.items():
        advance = original[name][0]
        change = (advance+da)//2 - advance//2 - dx
        if change:
            result[name] = change
    return result


def add_vertical_lookup(font, compensation):
    gpos = font['GPOS'].table
    order = font.getGlyphID
    names = sorted(compensation, key=order)
    sub = ot.SinglePos()
    sub.Format, sub.ValueFormat = 2, 0x1
    sub.Coverage = ot.Coverage()
    sub.Coverage.glyphs = names
    sub.Value = []
    for name in names:
        value = ValueRecord()
        value.XPlacement = compensation[name]
        sub.Value.append(value)
    sub.ValueCount = len(names)
    lookup = ot.Lookup()
    lookup.LookupType, lookup.LookupFlag = 1, 0
    lookup.SubTable, lookup.SubTableCount = [sub], 1
    gpos.LookupList.Lookup.append(lookup)
    index = len(gpos.LookupList.Lookup) - 1
    gpos.LookupList.LookupCount = index + 1
    attached = 0
    for record in gpos.FeatureList.FeatureRecord:
        if record.FeatureTag == 'vert':
            record.Feature.LookupListIndex.append(index)
            record.Feature.LookupCount = len(record.Feature.LookupListIndex)
            attached += 1
    assert attached
    return index, attached


def remove_features(gpos, tags):
    """Delete the features, then the lookups nothing else reaches, and renumber."""
    features = gpos.FeatureList.FeatureRecord
    keep = [i for i, record in enumerate(features) if record.FeatureTag not in tags]
    removed = [record for record in features if record.FeatureTag in tags]
    mapping = {old: new for new, old in enumerate(keep)}
    gpos.FeatureList.FeatureRecord = [features[i] for i in keep]
    gpos.FeatureList.FeatureCount = len(keep)
    for record in gpos.ScriptList.ScriptRecord:
        systems = [record.Script.DefaultLangSys] if record.Script.DefaultLangSys else []
        systems += [r.LangSys for r in record.Script.LangSysRecord]
        for system in systems:
            if system.ReqFeatureIndex != 0xFFFF:
                system.ReqFeatureIndex = mapping[system.ReqFeatureIndex]
            system.FeatureIndex = [mapping[i] for i in system.FeatureIndex if i in mapping]
            system.FeatureCount = len(system.FeatureIndex)
    used = {i for record in gpos.FeatureList.FeatureRecord for i in record.Feature.LookupListIndex}
    gone = {i for record in removed for i in record.Feature.LookupListIndex} - used
    lookups = gpos.LookupList.Lookup
    for lookup in lookups:
        for kind, _ in subtables(lookup):
            assert kind in (1, 2, 4, 5, 6), 'a lookup that can reference other lookups'
    survivors = [i for i in range(len(lookups)) if i not in gone]
    renumber = {old: new for new, old in enumerate(survivors)}
    gpos.LookupList.Lookup = [lookups[i] for i in survivors]
    gpos.LookupList.LookupCount = len(survivors)
    for record in gpos.FeatureList.FeatureRecord:
        record.Feature.LookupListIndex = [renumber[i] for i in record.Feature.LookupListIndex]
        record.Feature.LookupCount = len(record.Feature.LookupListIndex)
    return sorted(gone), len(removed)


def kern_pairs(font, palt_names):
    """Format 1 and 2 pair adjustments of the kern feature against the palt-adjusted glyphs."""
    gpos = font['GPOS'].table
    indexes = feature_lookups(gpos, 'kana', 'JAN ', 'kern')
    result = {'lookups': indexes, 'format1_pairs': 0, 'format1_pairs_between_palt_glyphs': 0,
              'format1_values': {}, 'format2_subtables': 0, 'format2_coverage_in_palt': 0}
    values = Counter()
    for index in indexes:
        for kind, sub in subtables(gpos.LookupList.Lookup[index]):
            assert kind == 2
            if sub.Format == 1:
                for first, pairs in zip(sub.Coverage.glyphs, sub.PairSet):
                    for pair in pairs.PairValueRecord:
                        result['format1_pairs'] += 1
                        if first in palt_names and pair.SecondGlyph in palt_names:
                            result['format1_pairs_between_palt_glyphs'] += 1
                            values[getattr(pair.Value1, 'XAdvance', 0)] += 1
            else:
                result['format2_subtables'] += 1
                result['format2_coverage_in_palt'] += sum(name in palt_names for name in sub.Coverage.glyphs)
    result['format1_values'] = {str(k): v for k, v in sorted(values.items())}
    return result


def build_face(source_stem, stem, bold):
    font = TTFont(OUT/(source_stem+'.ttf'), recalcTimestamp=False)
    style = 'Bold' if bold else 'Regular'
    gpos = font['GPOS'].table
    deltas, facts = palt_adjustments(font)
    original = {name: font['hmtx'][name] for name in deltas}
    kern = kern_pairs(font, set(deltas))
    halt = feature_lookups(gpos, 'kana', 'JAN ', 'halt')
    shift(font, deltas)
    anchors = shift_anchors(gpos, deltas)
    compensation = vertical_compensation(font, original, deltas)
    vertical_index, vertical_features = add_vertical_lookup(font, compensation)
    removed_lookups, removed_features = remove_features(gpos, {'palt', 'halt'})
    vertical_index = len(gpos.LookupList.Lookup) - 1
    names = set(deltas)
    facts.update({
        'glyphs': len(deltas), 'glyphs_with_placement': sum(1 for dx, _ in deltas.values() if dx),
        'glyphs_with_advance': sum(1 for _, da in deltas.values() if da),
        'composite_glyphs': sum(font['glyf'][n].isComposite() for n in names),
        'glyphs_with_cmap_entry': len(names & set(font.getBestCmap().values())),
        'halt_lookups': halt, 'removed_features': removed_features, 'removed_lookups': removed_lookups,
        'anchors_moved': anchors, 'vertical_compensated_glyphs': len(compensation),
        'vertical_features_extended': vertical_features, 'kern': kern})
    # Names follow sans.py: the same name IDs, the P family name and description.
    for nid, value in {1: FAMILY_P, 3: VERSION+';'+stem, 4: FAMILY_P+' '+style, 6: stem, 16: FAMILY_P,
                       10: DESCRIPTION}.items():
        font['name'].setName(value, nid, 3, 1, 0x409)
    for nid, value in {1: FAMILY_P_JA, 4: FAMILY_P_JA+' '+style, 16: FAMILY_P_JA}.items():
        font['name'].setName(value, nid, 3, 1, 0x411)
    font.save(OUT/(stem+'.ttf'))
    font.flavor = 'woff2'
    font.save(OUT/(stem+'.woff2'))
    (OUT/('sources-p-bold.json' if bold else 'sources-p.json')).write_text(json.dumps({
        'family': FAMILY_P, 'style': style, 'version': VERSION, 'base': source_stem,
        'baked_palt': facts, 'vertical_lookup_index': vertical_index,
    }, ensure_ascii=False, indent=2)+'\n')
    print(f'Built {FAMILY_P} {style} {VERSION}: {len(deltas)} palt glyphs, {len(compensation)} vertical compensations.',
          flush=True)


def build():
    build_face(STEM, STEM_P, False)
    build_face(BOLD_STEM, BOLD_STEM_P, True)
    notice = (OUT/'NOTICE.txt').read_text().replace('GenZui Sans / 源萃ゴシック\n',
                                                      'GenZui Sans P / 源萃ゴシックP\n\n'
                                                      'GenZui Sans with the palt widths of its kana and punctuation baked in.\n', 1)
    (OUT/'NOTICE-P.txt').write_text(notice)
    (OUT/'genzui-sans-p.css').write_text(''.join(
        f"@font-face {{\n  font-family: 'GenZui Sans P';\n  src: url('GenZuiSansP-{style}.woff2') format('woff2');\n"
        f"  font-weight: {weight};\n  font-style: normal;\n  font-display: swap;\n}}\n"
        for style, weight in (('Regular', 400), ('Bold', 700))))


if __name__ == '__main__':
    build()
