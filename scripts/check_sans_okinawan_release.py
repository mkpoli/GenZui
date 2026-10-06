"""Validate release contents and fail-closed staging safeguards."""
import json,os,tempfile
from pathlib import Path
from zipfile import ZipFile
from fontTools.ttLib import TTFont
import sans_okinawan_release as release
from sans_okinawan import PREFIX,VERSION,digest
from sources import ROOT


def check():
    files=release.checked_assets()
    counts={}
    for folder,prefix,count in [(release.FULL,'GenZuiSans',17096),(release.SUB,PREFIX,805)]:
        manifest=json.loads((folder/'staged-assets.json').read_text())
        expected=set(manifest)|{'staged-assets.json','browser-checks.json','preview.png'}
        with ZipFile(ROOT/'dist'/f'{prefix}-{VERSION}.zip') as z:
            assert set(z.namelist())==expected
            for name in expected:assert z.read(name)==(folder/name).read_bytes(),name
        for name,sha in manifest.items():assert digest(folder/name)==sha,name
        for style in ('Regular','Bold'):
            f=TTFont(folder/f'{prefix}-{style}.ttf');assert len(f.getBestCmap())==count
            assert f'{VERSION}' in f['name'].getDebugName(5)
        page=(folder/'index.html').read_text()
        assert page.count('title=')==70 and page.count('contenteditable="true"')==2
        assert 'previous/' not in page and 'variants/' not in page
        counts[prefix]=len(expected)
    # An unrelated file and a replaced full webfont must fail before packaging
    # or handing assets to the site. Work only in an isolated staging copy.
    original=release.FULL;original_root=release.ROOT
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='genzui-release-check-') as temp:
        stage=Path(temp)/'full';stage.mkdir()
        for path in original.iterdir():os.link(path,stage/path.name)
        release.FULL=stage;release.ROOT=Path(temp)/'scratch';release.ROOT.mkdir()
        try:
            (stage/'unrelated.ttf').write_bytes(b'not part of the release')
            try:release.package()
            except AssertionError:rejected.append('unexpected file')
            else:raise AssertionError('Unexpected file was packaged')
            (stage/'unrelated.ttf').unlink()
            bad=stage/'GenZuiSans-Regular.woff2';bad.unlink();bad.write_bytes(b'stale webfont')
            try:release.checked_assets()
            except AssertionError:rejected.append('changed full webfont')
            else:raise AssertionError('Replaced full webfont was accepted')
        finally:release.FULL=original;release.ROOT=original_root
    report=dict(status='passed',version=VERSION,archives=counts,public_assets=len(files),rejected=rejected)
    (ROOT/'research/sans-release-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':check()
