"""Compare compiled vowel ink breadth: 2 * filled area / contour perimeter.

This is an optical comparison aid, not a universal perceptual weight score.
Native and compact forms differ in proportions, junctions and terminals.
"""
import json
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from serif import contours
import okinawan_outline as O
from sans_okinawan import OUT,PREFIX,digest


def measure(pen):
    shape=pathops.Path();pen.replay(shape.getPen())
    shape=pathops.simplify(shape)
    result=RecordingPen();shape.draw(result)
    perimeter=0
    for ring in O.rings(result):
        for seg in ring:
            pts=np.array([O.point(seg,t) for t in np.linspace(0,1,129)])
            perimeter+=np.linalg.norm(np.diff(pts,axis=0),axis=1).sum()
    return round(float(2*shape.area/perimeter),2)


def report():
    rows=[]
    for style in ('Regular','Bold'):
        current=OUT/f'{PREFIX}-{style}.ttf';previous=OUT/'previous'/f'{style}.ttf'
        row=dict(style=style,current_sha256=digest(current),previous_sha256=digest(previous),before={},after={})
        for key,path in (('before',previous),('after',current)):
            f=TTFont(path)
            for cp,label in ((0xF45A,'HWA'),(0xF45B,'HWI'),(0xF45C,'HWE')):
                rings=O.rings(contours(f,cp))
                # The three native ふ contours begin left of x=500; all
                # detached vowel contours lie wholly to its right.
                vowel=[r for r in rings if min(p[0] for s in r for p in s)>500]
                assert len(rings)-len(vowel)==3,(style,label,len(rings),len(vowel))
                row[key][label]=measure(O.draw(vowel))
            row[key]['native_い']=measure(contours(f,ord('い')))
            row[key]['native_え_body']=measure(contours(f,ord('え'),[1]))
            row[key]['native_わ']=measure(contours(f,ord('わ')))
        rows.append(row)
    data=dict(method='2 × filled area / contour perimeter; font units; compiled vowel contours only',
              limitation='A comparison aid, sensitive to shape and terminals; verify visually at reading sizes.',faces=rows)
    (OUT/'fu-weight-measurements.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    return data

if __name__=='__main__':
    for row in report()['faces']:print(row['style'],row['before'],row['after'])
