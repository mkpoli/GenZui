"""Validate the matched Serif/Sans measurements and their displayed ratios."""
import json
from statistics import median
from sans_weight_audit import OUT, ROOT, digest


def check():
    parallel=json.loads((OUT/'parallel.json').read_text())
    results={}
    for family,folder,release,encoded in [('Sans',OUT,'sans-v0.104',16732),('Serif',OUT/'serif','v0.118',16726)]:
        revised=family=='Sans' and parallel[family]['release']!='sans-v0.104'
        if revised:folder=OUT/'revision'
        vectors=json.loads((folder/'vectors.json').read_text())
        strokes=json.loads((folder/'strokes.json').read_text())
        provenance=json.loads((folder/'provenance.json').read_text())
        index={(r['style'],r['origin'],r['text']):r for r in vectors}
        lookup={(r['style'],r['origin'],r['text'],r['pixels']):r for r in strokes}
        assert len(lookup)==len(strokes)==2268
        worst=0
        for style in ('Regular','Bold'):
            path=ROOT/f'releases/{release}/GenZui{family}-{style}.ttf'
            if revised:path=ROOT/f'build/sans-okinawan/full/GenZuiSans-{style}.ttf'
            assert provenance['faces'][style]['font_sha256']==parallel[family]['font_sha256'][style]==digest(path)
            assert len([r for r in vectors if r['style']==style and r['origin']=='Noto'])==encoded
            expected={r['text'] for r in parallel[family]['forms'] if r['style']==style}
            assert len(expected)==375
            for pixels in (512,1024):
                actual={r['text'] for r in strokes if r['style']==style and r['origin']=='GenZui' and r['pixels']==pixels}
                assert expected==actual
        for row in strokes:
            if row['pixels']!=1024:continue
            vector=index.get((row['style'],row['origin'],row['text']))
            if vector:
                difference=abs(row['ink_em_fraction']-vector['ink_em_fraction'])
                assert difference<.002,(family,row['style'],row['label'],difference)
                worst=max(worst,difference)
        for row in parallel[family]['forms']:
            if row['relative']:
                for q in ('q50','q75','q90'):
                    assert abs(row['relative'][q]*row['reference'][q]-row['stroke'][q])<1e-9
        results[family]=dict(native_encoded=encoded,comparison_forms=375,stroke_records=len(strokes),max_ink_area_error_em2=worst)
    assert {(r['style'],r['text']) for r in parallel['Sans']['forms']}=={(r['style'],r['text']) for r in parallel['Serif']['forms']}
    result=dict(status='passed',families=results)
    (OUT/'parallel-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':check()
