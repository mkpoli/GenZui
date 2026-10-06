"""Check coverage, raster/vector agreement and the numerical audit fixtures."""
import json
from sans_weight_audit import OUT, RELEASE, digest


def check():
    vectors = json.loads((OUT/'vectors.json').read_text(encoding='utf-8'))
    strokes = json.loads((OUT/'strokes.json').read_text(encoding='utf-8'))
    provenance = json.loads((OUT/'provenance.json').read_text(encoding='utf-8'))
    summary = json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    index = {(r['style'],r['origin'],r['text']):r for r in vectors}
    worst = 0
    for style in ('Regular','Bold'):
        assert provenance['faces'][style]['font_sha256'] == digest(RELEASE/f'GenZuiSans-{style}.ttf')
        assert len([r for r in vectors if r['style']==style and r['origin']=='Noto']) == 16732
        expected = {r['text'] for r in vectors if r['style']==style and r['origin']=='GenZui'}
        assert len(expected)==375
        assert {r['text'] for r in summary['forms'] if r['style']==style} == expected
        for pixels in (512,1024):
            assert {r['text'] for r in strokes if r['style']==style and r['pixels']==pixels and r['origin']=='GenZui'} == expected
    for r in strokes:
        if r['pixels'] != 1024 or (r['style'],r['origin'],r['text']) not in index:
            continue
        v = index[r['style'],r['origin'],r['text']]
        difference = abs(r['ink_em_fraction']-v['ink_em_fraction'])
        # A 0.002 em² tolerance covers raster edge quantization, while rejecting
        # clipping, fallback glyphs or shaping-inserted dotted circles.
        assert difference < .002, (r['style'],r['label'],difference)
        worst = max(worst,difference)
    assert max(r['error'] for r in provenance['calibration']) < 5
    assert len(summary['components']) == 6
    result = dict(status='passed', native_encoded_per_style=16732, comparison_forms_per_style=375,
                  stroke_records=len(strokes), resolutions=[512,1024], max_ink_area_error_em2=worst,
                  calibration_max_error_units=max(r['error'] for r in provenance['calibration']))
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    check()
