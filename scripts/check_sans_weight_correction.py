"""Bind the weight correction measurements to the final staged font bytes."""
import json
from sans_weight_audit import OUT, ROOT, digest
from sans_okinawan import OUT as PROOF,VERSION
from parallel_weight_report import analyze
from check_sans_okinawan import WEIGHT_CHANGES


def check():
    before=analyze(OUT);after=analyze(OUT/'revision')
    vectors=json.loads((OUT/'revision/vectors.json').read_text(encoding='utf-8'))
    vmap={(r['style'],r['origin'],r['text']):r for r in vectors}
    rows=json.loads((OUT/'revision/strokes.json').read_text(encoding='utf-8'))
    assert len(rows)==len({(r['style'],r['origin'],r['text'],r['pixels']) for r in rows})==2268
    details=[];worst=0
    for style in ('Regular','Bold'):
        assert after['font_sha256'][style]==digest(PROOF/'full'/f'GenZuiSans-{style}.ttf')
        old={r['text']:r for r in before['forms'] if r['style']==style}
        new={r['text']:r for r in after['forms'] if r['style']==style}
        assert old.keys()==new.keys() and len(new)==375
        for r in new.values():
            if r['label'] not in WEIGHT_CHANGES[style]:continue
            previous=old[r['text']]
            direction=-1 if style=='Regular' and r['label'] in ('KWE','GWE','SI','ZI') else 1
            assert direction*(r['stroke']['q50']-previous['stroke']['q50'])>0,(style,r['label'],'wrong correction direction')
            details.append(dict(style=style,label=r['label'],before_median=previous['stroke']['q50'],after_median=r['stroke']['q50'],
                                before_relative_75th=previous['relative']['q75'],after_relative_75th=r['relative']['q75']))
        for q in ('q50','q75','q90'):
            old_group=next(r for r in before['groups'] if r['style']==style and r['group']=='funatsu')['metrics'][q]
            new_group=next(r for r in after['groups'] if r['style']==style and r['group']=='funatsu')['metrics'][q]
            assert new_group['relative_iqr_pct']<old_group['relative_iqr_pct'],(style,q,'spread did not improve')
        hentaigana=next(r for r in after['groups'] if r['style']==style and r['group']=='hentaigana')
        assert .95<=hentaigana['metrics']['q75']['relative']['q50']<=1.05,(style,'hentaigana calibration')
    for row in rows:
        if row['pixels']!=1024:continue
        v=vmap.get((row['style'],row['origin'],row['text']))
        if v:
            error=abs(row['ink_em_fraction']-v['ink_em_fraction']);worst=max(worst,error)
            assert error<.002,(row['style'],row['label'],error)
    summary=dict(status='passed',version=VERSION,font_sha256=after['font_sha256'],comparison_forms=375,
                 raster_records=len(rows),max_ink_area_error_em2=worst,changes=details,
                 groups_before=[r for r in before['groups'] if r['group'] in ('funatsu','hentaigana')],
                 groups_after=[r for r in after['groups'] if r['group'] in ('funatsu','hentaigana')])
    raw=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
    (ROOT/'research/sans-weight-correction.json').write_text(raw, encoding='utf-8')
    (OUT/'weight-correction-checks.json').write_text(raw, encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('groups_before','groups_after','changes')}))


if __name__=='__main__':check()
