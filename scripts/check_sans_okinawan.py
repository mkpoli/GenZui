"""Check the Sans Okinawan extension, preserved baseline, and subset shaping."""
import json
import uharfbuzz as hb
import numpy as np
import pathops
from scipy.spatial import cKDTree
import okinawan_sans as drawings
import okinawan_outline as O
from serif import contours,transform,instance
from fontTools.pens.boundsPen import BoundsPen
from okinawan import DAKUTEN
from fontTools.ttLib import TTFont
from sans_okinawan import OUT,BASE,PREFIX,FAMILY,digest
from okinawan import ENTRIES,PUA
from okinawan_subset import repertoire
from okinawan_sns import SENTENCES,compose
from check_okinawan_subset import outline,shaped

def geometry(weight):
    def shape(parts):
        result=pathops.Path()
        for part in parts:
            p=pathops.Path();part.replay(p.getPen());result=pathops.op(result,p,pathops.PathOp.UNION)
        return result
    def points(parts):
        return np.array([O.point(seg,t) for part in parts for ring in O.rings(part)
                         for seg in ring for t in np.linspace(0,1,31)])
    recipes=drawings.drawings(weight);clearances={}
    for cp in DAKUTEN:
        base=recipes[cp]
        marks=drawings.voiced_parts(drawings.source(weight),cp,base,contours,transform)[len(base):]
        assert pathops.op(shape(base),shape(marks),pathops.PathOp.INTERSECTION).area<.01,(weight,hex(cp))
        gap=float(cKDTree(points(base)).query(points(marks))[0].min())
        # Sampling verifies an optical margin in addition to exact non-intersection.
        assert gap>=18,(weight,hex(cp),gap)
        clearances[f'U+{cp:04X}']=round(gap,2)
    for cp,a,b in [(0xF469,0,1),(0xF45A,1,3)]:
        assert pathops.op(shape([recipes[cp][a]]),shape([recipes[cp][b]]),pathops.PathOp.INTERSECTION).area<.01,(weight,hex(cp))
    component_gaps={}
    # Marks, detached vowels and the glottal prefix must retain whitespace in
    # Bold as well as Regular; the former top marks nearly touched their bases.
    for cp in (0xF460,0xF461,0xF462,0xF463,0xF467,0xF45E,0xF45F,0xF452):
        a,b=recipes[cp][:1],recipes[cp][1:]
        assert pathops.op(shape(a),shape(b),pathops.PathOp.INTERSECTION).area<.01,(weight,hex(cp))
        gap=float(cKDTree(points(a)).query(points(b))[0].min())
        assert gap>=35,(weight,hex(cp),gap)
        component_gaps[f'U+{cp:04X}']=round(gap,2)
    detached=recipes
    for cp in (0xF45A,0xF45B,0xF45C):
        body,dot=detached[cp][1:2],detached[cp][2:3]
        assert pathops.op(shape(body),shape(dot),pathops.PathOp.INTERSECTION).area<.01,(weight,hex(cp),'left dot')
        assert float(cKDTree(points(body)).query(points(dot))[0].min())>=28,(weight,hex(cp),'left dot')
        a,b=detached[cp][:3],detached[cp][3:]
        assert pathops.op(shape(a),shape(b),pathops.PathOp.INTERSECTION).area<.01,(weight,hex(cp),'detached')
        gap=float(cKDTree(points(a)).query(points(b))[0].min())
        assert gap>=30,(weight,hex(cp),'detached',gap)
    return clearances,component_gaps

def check():
    (OUT/'checks.json').unlink(missing_ok=True)
    records=[]
    manifest=json.loads((OUT/'sources.json').read_text())
    for style in ('Regular','Bold'):
        original=TTFont(BASE/f'GenZuiSans-{style}.ttf',recalcTimestamp=False)
        full_path=OUT/'full'/f'GenZuiSans-{style}.ttf'
        full=TTFont(full_path,recalcTimestamp=False)
        web_full=TTFont(full_path.with_suffix('.woff2'),recalcTimestamp=False)
        sub=TTFont(OUT/f'{PREFIX}-{style}.ttf',recalcTimestamp=False)
        web=TTFont(OUT/f'{PREFIX}-{style}.woff2',recalcTimestamp=False)
        oc,fc,sc=original.getBestCmap(),full.getBestCmap(),sub.getBestCmap()
        assert len(oc)==17070 and set(fc)==set(oc)|set(PUA)
        assert len(fc)==17096 and sc.keys()==repertoire(full)==web.getBestCmap().keys()
        old_order=original.getGlyphOrder()
        assert full.getGlyphOrder()[:len(old_order)]==old_order
        for name in old_order:
            assert original['glyf'][name].compile(original['glyf'])==full['glyf'][name].compile(full['glyf']),name
            for tag in ('hmtx','vmtx'):assert original[tag][name]==full[tag][name],(tag,name)
        for cp in sc:
            assert outline(full,fc[cp])==outline(sub,sc[cp])==outline(web,web.getBestCmap()[cp]),hex(cp)
            for tag in ('hmtx','vmtx'):assert full[tag][fc[cp]]==sub[tag][sc[cp]]==web[tag][web.getBestCmap()[cp]]
        assert full.getGlyphOrder()==web_full.getGlyphOrder()
        for name in full.getGlyphOrder():
            assert outline(full,name)==outline(web_full,name),name
            for tag in ('hmtx','vmtx'):assert full[tag][name]==web_full[tag][name]
        for font in (sub,web):
            assert font['name'].getDebugName(1)==FAMILY
            assert font['name'].getName(1,3,1,0x411).toUnicode()=='源萃ゴシック 沖縄文字'
            assert font['name'].getDebugName(6)==f'{PREFIX}-{style}'
            assert font['OS/2'].usWeightClass==(400 if style=='Regular' else 700)
            assert font['OS/2'].fsType==original['OS/2'].fsType
            for n in (0,13,14):assert font['name'].getDebugName(n)==original['name'].getDebugName(n)
            for tag in ('hhea','vhea'):
                for attr in ('ascent','descent','lineGap'):assert getattr(font[tag],attr)==getattr(original[tag],attr)
        # Every previously encoded character still shapes identically in both directions.
        for cp in oc:
            for direction in ('ltr','ttb'):
                assert shaped(original,chr(cp),direction)==shaped(full,chr(cp),direction),(style,hex(cp),direction)
        examples=[chr(cp) for cp in sc]+['a\u0301','カ\u3099','ﾊﾟ','「しまくとぅば。」']
        examples+=[''.join(chr(int(cp,16)) for cp in e['output']) for e in ENTRIES]+[compose(s['text']) for s in SENTENCES]
        for text in examples:
            for direction in ('ltr','ttb'):
                assert shaped(full,text,direction)==shaped(sub,text,direction)==shaped(web,text,direction),(style,repr(text),direction)
        for e in ENTRIES:
            text=''.join(chr(int(cp,16)) for cp in e['output'])
            if len(e['output'])==2 and int(e['output'][0],16) in PUA:
                assert len(shaped(full,text))==1,e['id']
                base=full['glyf'][fc[int(e['output'][0],16)]]
                buffer=hb.Buffer();buffer.add_str(text);buffer.guess_segment_properties()
                hb.shape(full._audit_hb,buffer)
                voiced=full['glyf'][full.getGlyphName(buffer.glyph_infos[0].codepoint)]
                assert voiced.numberOfContours==base.numberOfContours+2,e['id']
            if e['system']=='prefecture':
                assert sub['hmtx'][sc[ord(text)]][0]==500
                pen=BoundsPen(None)
                for part in drawings.raised_parts(400 if style=='Regular' else 700,chr(int(e['base'],16))):part.replay(pen)
                g=sub['glyf'][sc[ord(text)]]
                assert all(abs(a-b)<=2 for a,b in zip((g.xMin,g.yMin,g.xMax,g.yMax),pen.bounds))
            if e['id'] in ('hwa','hwi','hwe'):
                g=sub['glyf'][sc[ord(text)]]
                assert 0<=g.xMin<g.xMax<=1000
        record=next(r for r in manifest['faces'] if r['style']==style)
        assert record['base_sha256']==digest(BASE/f'GenZuiSans-{style}.ttf')
        assert record['full_sha256']==digest(full_path)
        for ext in ('ttf','woff2'):assert record[ext+'_sha256']==digest(OUT/f'{PREFIX}-{style}.{ext}')
        dakuten_gaps,component_gaps=geometry(400 if style=='Regular' else 700)
        records.append(dict(record,full_encoded_characters=len(fc),preserved_glyphs=len(old_order),forms=35,
                            dakuten_clearance_units=dakuten_gaps,component_clearance_units=component_gaps))
        print(style,'passed: baseline, full font, subset and horizontal/vertical shaping',flush=True)
    variants=check_variants()
    from sans_okinawan_candidates import check as check_candidates
    candidates=check_candidates(OUT)
    (OUT/'checks.json').write_text(json.dumps(dict(status='passed',faces=records,proof_variants=variants,proof_candidates=candidates),indent=2)+'\n')

def check_variants():
    variants=json.loads((OUT/'variants/manifest.json').read_text())
    for record in variants:
        path=OUT/record['file'];assert digest(path)==record['sha256']
        web=TTFont(path);ttf=TTFont(path.with_suffix('.ttf'))
        assert web['name'].getDebugName(1)==record['family']
        assert web.getBestCmap().keys()==ttf.getBestCmap().keys()
        for cp,name in web.getBestCmap().items():
            tn=ttf.getBestCmap()[cp]
            assert outline(web,name)==outline(ttf,tn)
            for tag in ('hmtx','vmtx'):assert web[tag][name]==ttf[tag][tn]
        raised=[e for e in ENTRIES if e['system']=='prefecture']
        family='NotoSerifJP' if 'Serif' in record['family'] else 'NotoSansJP'
        donor=instance(family,record['donor'],{int(e['base'],16) for e in raised})
        for e in raised:
            name=web.getBestCmap()[int(e['output'][0],16)]
            assert web['hmtx'][name][0]==500
            bounds=BoundsPen(None)
            transform(contours(donor,int(e['base'],16)),(.48,0,0,.48,10,410)).replay(bounds)
            actual=web['glyf'][name]
            assert all(abs(a-b)<=2 for a,b in zip((actual.xMin,actual.yMin,actual.xMax,actual.yMax),bounds.bounds)),(record['file'],e['id'])
    return variants

if __name__=='__main__':check()
