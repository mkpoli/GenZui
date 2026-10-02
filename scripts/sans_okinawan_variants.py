"""Local proof alternatives; these do not alter the shipped family drawings."""
import hashlib
import json
import pathops
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from serif import instance, contours, transform, glyph
from kugyol import rename, parent_name
from okinawan import ENTRIES
import okinawan_sans


def build(out, root, version):
    dest=out/'variants';dest.mkdir(exist_ok=True)
    raised=[e for e in ENTRIES if e['system']=='prefecture']
    records=[]
    specs=[('Sans',style,'Detached',None) for style in ('Regular','Bold')]
    specs += [('Serif','Regular','Optical',500),('Serif','Bold','Optical',750),('Sans','Regular','Optical',450)]
    for family,style,kind,donor_weight in specs:
        source=(out/f'GenZuiSansOkinawan-{style}.ttf' if family=='Sans' else
                root/'releases/v0.118'/f'GenZuiSerifOkinawan-{style}.ttf')
        font=TTFont(source,recalcTimestamp=False)
        notices=[parent_name(font,n) for n in (0,13,14)]
        if kind=='Detached':
            recipes=okinawan_sans.drawings(400 if style=='Regular' else 700,detached=True)
            replacements={cp:recipes[cp] for cp in (0xF45A,0xF45B,0xF45C)}
        else:
            donor=instance('Noto'+family+'JP',donor_weight,{int(e['base'],16) for e in raised})
            replacements={int(e['output'][0],16):[transform(contours(donor,int(e['base'],16)),(.48,0,0,.48,10,410))] for e in raised}
            options=subset.Options();options.layout_features=['*'];options.recalc_timestamp=False
            sub=subset.Subsetter(options=options)
            sub.populate(unicodes=set(replacements)|{int(e['base'],16) for e in raised});sub.subset(font)
        cmap=font.getBestCmap()
        for cp,parts in replacements.items():
            merged=pathops.Path()
            for part in parts:
                p=pathops.Path();part.replay(p.getPen());merged=pathops.op(merged,p,pathops.PathOp.UNION)
            pen=RecordingPen();merged.draw(pen);g=glyph([pen]);name=cmap[cp]
            font['glyf'][name]=g;g.recalcBounds(font['glyf'])
            font['hmtx'][name]=(font['hmtx'][name][0],g.xMin)
            font['vmtx'][name]=(font['vmtx'][name][0],880-g.yMax)
        face=f'GenZui {family} Okinawan {kind}'
        stem=f'GenZui{family}Okinawan{kind}-{style}'
        rename(font,face,face,style,stem,version,*notices)
        font.save(dest/f'{stem}.ttf');font.flavor='woff2';font.save(dest/f'{stem}.woff2')
        # Serialize and check each alternative's actual cmap and metrics.
        web=TTFont(dest/f'{stem}.woff2');assert set(replacements)<=web.getBestCmap().keys()
        for cp in replacements:
            assert web['hmtx'][web.getBestCmap()[cp]][0]==(500 if kind=='Optical' else 1000)
        records.append(dict(family=face,style=style,kind=kind,donor=donor_weight,file=f'variants/{stem}.woff2',
                            sha256=hashlib.sha256((dest/f'{stem}.woff2').read_bytes()).hexdigest()))
    (dest/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    return records
