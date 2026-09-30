"""Build the native-range and before/after review for Okinawan weight corrections."""
import hashlib
import html
import json
import shutil
from pathlib import Path
import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from okinawan_weight_audit import OUT
from serif import font_path
from sources import ROOT

NOTES = {
 'TU':'Heavy strokes supported by the measurements; lighter と/つ masters, with the accepted return retained.',
 'TI':'Small horizontal-arm deficit; add at most 2.5 units beneath the arm. The elbow and right stroke stay intact.',
 'KWA':'Heavy upright strokes in わ; reduce its donor from 700 to 600 and slightly lighten く. Keep the continuous sweep.',
 'KWI':'Overall median was close to native く/い, but its upper quartile and reduced components were heavy. Reduce both donor weights.',
 'KWE':'Modest optical reduction in く, the reduced え and its foot; overall width was already near the donors.',
 'HWA':'No whole-glyph thickness excess over ふ. Small optical reduction in わ and shoulder; native ふ body retained.',
 'HWI':'No whole-glyph thickness excess over ふ. Small optical reduction in the reduced い; native ふ body retained.',
 'HWE':'No whole-glyph thickness excess over ふ. Small optical reduction in え and shoulder; native ふ body retained.',
 'Glottal YA':'Native や stroke widths were already close. Relieve only the added mark and its join.',
 'Glottal YO':'Native よ median was close. Reduce the added mark and some sideways compensation.',
 'TSI':'Whole-glyph median was below native つ; only a small optical reduction of the fuller つ component.',
 'WU':'Retained as a control.', 'SI':'Retained as a control.', 'Glottal YU':'Retained as a control.',
 'Glottal WA':'Retained as a control.', 'Glottal WI':'Retained as a control.', 'Glottal WE':'Retained as a control.',
 'Glottal N':'Native ん body retained. No change pending clarification of the weight concern.',
 'YI':'Native い body is unchanged; the added dakuten changes whole-glyph statistics.',
 'YE':'Native え body is unchanged; the added dakuten changes whole-glyph statistics.',
}
VOICE = dict(DU='TU',DI='TI',GWA='KWA',GWI='KWI',GWE='KWE',ZI='SI',DZI='TSI')

def read(name):return json.loads((OUT/name).read_text())

def build():
    before,after=read('before-1024.json'),read('after-1024.json')
    native=read('native-vector.json'); strokes=read('native-strokes-1024.json')
    # Reject directional estimates with poor support or unstable resolution.
    for phase,hi,key in [('native-strokes',strokes,'text'),('before',before,'label'),('after',after,'label')]:
        lo={(r['style'],r[key]):r for r in read(f'{phase}-512.json')}
        for r in hi:
            lower=lo[r['style'],r[key]]
            for direction,quantiles in r['directions'].items():
                q=lower['directions'][direction]
                if not q or not quantiles or abs(quantiles['q50']/q['q50']-1)>.10:
                    r['directions'][direction]=None
    lookup={(r['style'],r['text']):r for r in strokes}
    nlookup={(r['style'],r['text']):r for r in native}
    rows=[]
    for a,b in zip(before,after):
        assert (a['style'],a['label'])==(b['style'],b['label'])
        label=a['label']; delta=100*(b['area']/a['area']-1)
        rows.append(dict(label=label,style=a['style'],text=a['text'],donors=a['donors'],before=a,after=b,
                         ink_change_percent=delta,native=[dict(vector=nlookup[a['style'],ch],**lookup[a['style'],ch]) for ch in a['donors']],
                         note=NOTES.get(VOICE.get(label,label),'')))
    cohorts=[]
    for style in ('Regular','Bold'):
        for script in sorted({r['script'] for r in native}):
            group={r['glyph']:r for r in native if r['style']==style and r['script']==script and r['area']>0}
            if not group:continue
            values=[r['effective_width'] for r in group.values()]
            cohorts.append(dict(style=style,script=script,count=len(values),quantiles=np.percentile(values,[0,10,25,50,75,90,100]).tolist()))
    stability={}
    for phase in ('before','after'):
        lo={(r['style'],r['label']):r for r in read(f'{phase}-512.json')}
        hi=before if phase=='before' else after
        stability[phase]=max(abs(r['stroke']['q50']/lo[r['style'],r['label']]['stroke']['q50']-1)*100 for r in hi)
    data=dict(source=read('native-source.json'),environment=read('environment.json'),snapshots={p:read(f'{p}-source.json') for p in ('before','after')},
              method=dict(em=1000,pixels=1024,validation_pixels=512,metric='2 × union area / outline perimeter',
                          stroke='Arc-length-weighted medial-axis diameter; junction/terminal neighbourhoods excluded.',
                          direction_min_axis_units=60,units='font units, at a fixed 1000-unit em',
                          limitation='Geometry describes thickness, density and contrast; it does not prove equal perceived weight.'),
              max_custom_median_resolution_change_percent=stability,cohorts=cohorts,characters=rows)
    (OUT/'report.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (ROOT/'research/okinawan-weight-audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    # The original variable font supplies every native table character at both weights.
    shutil.copyfile(font_path('NotoSerifJP'),OUT/'native.ttf')
    points=set(range(0x20,0x7f))|set(range(0x3040,0x3100))|{int(cp,16) for r in before for cp in r['codepoints']}
    for phase in ('before','after'):
        for style in ('Regular','Bold'):
            f=TTFont(OUT/f'{phase}-{style}.ttf',recalcTimestamp=False)
            sub=subset.Subsetter();sub.populate(unicodes=points);sub.subset(f);f.flavor='woff2'
            f.save(OUT/f'{phase}-{style}.woff2')
    template=(ROOT/'templates/okinawan-weight/index.html').read_text()
    (OUT/'index.html').write_text(template)
    # A static companion makes the same-size comparison inspectable without a browser.
    labels=['TU','TI','KWA','KWI','KWE','HWA','HWI','HWE','Glottal YA','Glottal YO','TSI','WU']
    im=Image.new('RGB',(1440,len(labels)*155+65),'#f7f8f2');d=ImageDraw.Draw(im)
    native_face=ImageFont.truetype(str(font_path('NotoSerifJP')),115);native_face.set_variation_by_axes([400])
    old=ImageFont.truetype(str(OUT/'before-Regular.ttf'),115);new=ImageFont.truetype(str(OUT/'after-Regular.ttf'),115)
    ui=ImageFont.truetype('DejaVuSans.ttf',20)
    for x,t in [(25,'Regular'),(200,'Native donors'),(680,'Before'),(1060,'Adjusted')]:d.text((x,20),t,font=ui,fill='#254532')
    for i,label in enumerate(labels):
        r=next(r for r in rows if r['style']=='Regular' and r['label']==label);y=65+i*155
        d.line((20,y+122,1420,y+122),fill='#d1d9d0');d.text((25,y+70),label,font=ui,fill='#254532')
        for x,text,font in [(200,r['donors'],native_face),(680,r['text'],old),(1060,r['text'],new)]:
            d.text((x,y+115),text,font=font,fill='#111',anchor='ls')
    im.save(OUT/'regular-contact.png')
    print('Weight report: 27 forms × 2 weights, all native encoded characters, source context and before/after.')

if __name__=='__main__':build()
