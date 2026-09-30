"""Verify the Okinawan subset against the full fonts, including shaped forms."""
import io
import json
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from okinawan_subset import OUT,PARENT,PREFIX,FAMILY,FAMILY_JA,repertoire,digest
from okinawan import ENTRIES
from okinawan_sns import SENTENCES,compose
from sources import ROOT

def outline(font,name):
    if not hasattr(font,'_audit_glyphset'):font._audit_glyphset=font.getGlyphSet()
    gs=font._audit_glyphset;p=DecomposingRecordingPen(gs);gs[name].draw(p);return p.value

def shaped(font,text,direction='ltr'):
    if not hasattr(font,'_audit_hb'):
        font.flavor=None;stream=io.BytesIO();font.save(stream)
        font._audit_hb=hb.Font(hb.Face(stream.getvalue()));font._audit_hb.scale=(1000,1000)
    face=font._audit_hb
    b=hb.Buffer();b.add_str(text);b.guess_segment_properties();b.direction=direction
    hb.shape(face,b)
    assert all(g.codepoint for g in b.glyph_infos),repr(text)
    return [(outline(font,font.getGlyphName(g.codepoint)),(p.x_advance,p.y_advance,p.x_offset,p.y_offset)) for g,p in zip(b.glyph_infos,b.glyph_positions)]

def check():
    records=[]
    source=json.loads((OUT/'sources.json').read_text())
    for style in ('Regular','Bold'):
        parent_path=PARENT/f'GenZuiSerif-{style}.ttf';parent=TTFont(parent_path)
        sub=TTFont(OUT/f'{PREFIX}-{style}.ttf');web=TTFont(OUT/f'{PREFIX}-{style}.woff2')
        pc,sc=parent.getBestCmap(),sub.getBestCmap();expected=repertoire(parent)
        assert set(sc)==expected==set(web.getBestCmap())
        for cp in expected:
            a,b=pc[cp],sc[cp]
            assert outline(parent,a)==outline(sub,b)==outline(web,web.getBestCmap()[cp]),hex(cp)
            for tag in ('hmtx','vmtx'):assert parent[tag][a]==sub[tag][b]==web[tag][web.getBestCmap()[cp]],(tag,hex(cp))
        assert sub['name'].getDebugName(1)==FAMILY
        assert sub['name'].getName(1,3,1,0x411).toUnicode()==FAMILY_JA
        assert sub['name'].getDebugName(6)==f'{PREFIX}-{style}'
        assert sub['OS/2'].usWeightClass==(400 if style=='Regular' else 700)
        for nid in (0,5,13,14):assert sub['name'].getDebugName(nid)==parent['name'].getDebugName(nid)
        assert sub['OS/2'].fsType==parent['OS/2'].fsType
        for tag in ('hhea','vhea'):
            for attr in ('ascent','descent','lineGap'):assert getattr(sub[tag],attr)==getattr(parent[tag],attr)
        examples=[chr(cp) for cp in sorted(expected)]+['a\u0301','カ\u3099','ﾊﾟ','「しまくとぅば。」']+[''.join(chr(int(cp,16)) for cp in e['output']) for e in ENTRIES]+[compose(s['text']) for s in SENTENCES]
        for text in examples:
            for direction in ('ltr','ttb'):
                assert shaped(parent,text,direction)==shaped(sub,text,direction)==shaped(web,text,direction),(style,repr(text),direction)
        for e in ENTRIES:
            if e['system']=='prefecture':assert sub['hmtx'][sc[int(e['output'][0],16)]][0]==500
        original=next(r for r in source['faces'] if r['style']==style)
        assert original['parent_sha256']==digest(parent_path)
        record=dict(style=style,encoded_characters=len(expected),forms=35,parent_sha256=digest(parent_path),
                    **{ext+'_sha256':digest(OUT/f'{PREFIX}-{style}.{ext}') for ext in ('ttf','woff2')})
        for ext in ('ttf','woff2'):assert record[ext+'_sha256']==original[ext+'_sha256']
        records.append(record)
    report=dict(family=FAMILY,status='passed',faces=records)
    raw=json.dumps(report,indent=2)+'\n';(OUT/'checks.json').write_text(raw);(ROOT/'research/okinawan-subset-checks.json').write_text(raw)
    print('Okinawan subset passed: exact repertoire, native outlines/metrics, names, every encoded character, 35 forms, sentences, vertical shaping and TTF/WOFF2 parity.')

if __name__=='__main__':check()
