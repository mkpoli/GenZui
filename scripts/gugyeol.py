"""구결자 (Korean gugyeol) at the Hanyang private-use convention.

181 of the 255 registered forms have a `twin`: a CJK ideograph whose shape
the Haansoft form reproduces. Each such form is drawn from that ideograph's
own outline: the face's own glyph when the twin is already encoded in the
built font (so it matches the face's style exactly), otherwise the pinned
Noto CJK JP source for the face, exactly as honkoku.py copies 卄. Forms with
`twin: null` in the registry have no drawing yet and stay unencoded.
"""
import copy
import json

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

from sources import ROOT

DATA = json.loads((ROOT/'data/gugyeol/forms.json').read_text())
FORMS = DATA['forms']
TWINS = {int(f['codepoint'], 16): int(f['twin'], 16) for f in FORMS if f['twin']}
TWIN_CHARS = {int(f['codepoint'], 16): f['twin_char'] for f in FORMS if f['twin']}
PUA = tuple(sorted(TWINS))


def add_gugyeol(font, add, make_glyph, source, cjk_label):
    """Append the 181 drawable 구결자 and return {codepoint: description}.

    `source` is the pinned Noto CJK JP OTF for this face, used only for the
    twins absent from the face's own base. `cjk_label` names that source in
    the returned provenance text.
    """
    cmap = font.getBestCmap()
    for cp in PUA:
        assert cp not in cmap, f'U+{cp:04X} is already mapped'
    descriptions = {}
    with TTFont(source) as donor:
        assert donor['head'].unitsPerEm == font['head'].unitsPerEm == 1000
        donor_cmap = donor.getBestCmap()
        donor_glyphs = donor.getGlyphSet()
        for cp in PUA:
            twin, twin_char = TWINS[cp], TWIN_CHARS[cp]
            if twin in cmap:
                name = cmap[twin]
                outline = copy.deepcopy(font['glyf'][name])
                gname = add(font, f'gugyeol.u{cp:04X}', outline)
                font['hmtx'][gname] = font['hmtx'][name]
                if name in font['vmtx'].metrics:
                    font['vmtx'][gname] = font['vmtx'][name]
                note = f"the face's own glyph of {twin_char} U+{twin:04X}"
            else:
                assert twin in donor_cmap, (
                    f'twin U+{twin:04X} for U+{cp:04X} is missing from the face and from {source.name}')
                dname = donor_cmap[twin]
                pen = RecordingPen()
                donor_glyphs[dname].draw(pen)
                outline = make_glyph([pen])
                gname = add(font, f'gugyeol.u{cp:04X}', outline)
                font['hmtx'][gname] = donor['hmtx'][dname]
                origin = donor['VORG'].VOriginRecords.get(dname, donor['VORG'].defaultVertOriginY)
                font['vmtx'][gname] = (1000, origin - outline.yMax)
                note = f'{cjk_label} of {twin_char} U+{twin:04X}'
            font['GDEF'].table.GlyphClassDef.classDefs[gname] = 1
            for table in font['cmap'].tables:
                if table.isUnicode() and table.format in (4, 12):
                    table.cmap[cp] = gname
            descriptions[cp] = (
                f'구결자 in the Hanyang private-use convention, drawn from {note}. '
                'The code point is private use, not a Unicode character assignment.')
    return descriptions
