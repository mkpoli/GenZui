"""Check release links, font identity, public copy and share assets."""
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from zipfile import ZipFile

from PIL import Image

from release_site import OUT, URL
from serif import VERSION, STEM
from sources import ROOT


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href','src','data-src') and value:
                self.links.append(value)


def check():
    manifest=json.loads((OUT/'release.json').read_text())
    checks=json.loads((ROOT/'build/serif/checks.json').read_text())
    assert manifest['version']==VERSION and manifest['font_sha256']==checks['ttf_sha256']
    count=0
    for name,expected in manifest['files'].items():
        p=OUT/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,name
        if p.suffix not in ('.html','.txt','.js','.css','.json','.svg','.xml'):continue
        text=p.read_text()
        assert not re.search(r'/home/[A-Za-z0-9_.-]+/',text),name
        assert 'CodexArtifacts' not in text,name
        if p.suffix!='.html':continue
        assert '{{' not in text,name
        parser=Links();parser.feed(text)
        for link in parser.links:
            parts=urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:continue
            target=OUT/parts.path.lstrip('/') if parts.path.startswith('/') else p.parent/unquote(parts.path)
            assert target.resolve().is_relative_to(OUT.resolve()),(name,link)
            if target.is_dir():target=target/'index.html'
            elif not target.is_file() and not target.suffix:target=target.with_suffix('.html')
            assert target.is_file(),(name,link)
            count+=1
    for route in ('index.html','gallery.html','minnan.html'):
        text=(OUT/route).read_text()
        assert 'name="twitter:card" content="summary_large_image"' in text
        assert f'{URL}/media/genzui-social.png' in text
        assert 'data:font/' not in text
    home=(OUT/'index.html').read_text();gallery=(OUT/'gallery.html').read_text()
    assert 'https://kureedo.mkpo.li/' in home
    visible_gallery=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', gallery, flags=re.S)
    for review in ('Swap to','>Accepted<','KOTO E:','0.107','0.108','class="sample before"'):
        assert review not in visible_gallery,review
    assert gallery.count('class="glyph-card"')==21
    assert 'value="hooked"' in gallery and 'value="curved"' in gallery
    for suffix in ('ttf','woff2'):
        for folder in ('downloads','v'+VERSION):
            actual=hashlib.sha256((OUT/folder/(STEM+'.'+suffix)).read_bytes()).hexdigest()
            assert actual==checks[suffix+'_sha256']
    with ZipFile(OUT/'downloads'/f'{STEM}-{VERSION}.zip') as z:
        assert z.testzip() is None
        assert hashlib.sha256(z.read(STEM+'.ttf')).hexdigest()==checks['ttf_sha256']
        assert {'OFL.txt','NOTICE.txt','FRB-OFL.txt','NotoSerifCJK-OFL.txt','Unicode-LICENSE.txt'}<=set(z.namelist())
        coverage=json.loads(z.read('kana-coverage.json'))
        assert coverage['font_sha256']==checks['ttf_sha256']
        assert coverage['coverage']['Script plus Script_Extensions']=={
            'total':763,'covered':763,'missing':[]}
        assert json.loads((OUT/'downloads/kana-coverage.json').read_text())==coverage
    assert Image.open(OUT/'media/genzui-social.png').size==(1200,630)
    assert Image.open(OUT/'media/genzui-social-2x.png').size==(2400,1260)
    data=json.loads(next((OUT/'assets').glob('characters-*.json')).read_text())
    assert data['total']==17064 and len(data['characters'])==17064
    assert sum(c['source']=='genzui' for c in data['characters'])==32
    report={'version':VERSION,'font_sha256':checks['ttf_sha256'],'local_links_checked':count,
            'public_gallery_forms':21,'release_files_checked':len(manifest['files']),
            'font_bytes_unchanged':True,'status':'passed'}
    (ROOT/'research/release-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
