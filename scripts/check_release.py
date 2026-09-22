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
from okinawan import PUA as OKINAWAN_PUA, DATA as OKINAWAN_DATA
from sans_site import STEM as SANS_STEM, checked as sans_checked
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
    for route in ('index.html','gallery.html','minnan.html','sans.html'):
        text=(OUT/route).read_text()
        assert 'name="twitter:card" content="summary_large_image"' in text
        image='genzui-sans-social.png' if route=='sans.html' else 'genzui-social.png'
        assert f'{URL}/media/{image}' in text
        assert 'data:font/' not in text
    home=(OUT/'index.html').read_text();gallery=(OUT/'gallery.html').read_text()
    assert 'https://kureedo.mkpo.li/' in home
    assert 'og:title" content="源萃 — GenZui Serif / GenZui Sans"' in home and 'GenZui Sans (源萃ゴシック)' in home
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
    assert Image.open(OUT/'media/genzui-sans-social.png').size==(1200,630)
    assert Image.open(OUT/'media/genzui-sans-social-2x.png').size==(2400,1260)
    sans_version,sans_checks,_=sans_checked()
    assert manifest['sans_version']==sans_version and manifest['sans_font_sha256']==sans_checks['ttf_sha256']
    sans=(OUT/'sans.html').read_text()
    assert f'sans-v{sans_version}/{SANS_STEM}.woff2' in sans and f'v{VERSION}/{STEM}.woff2' in sans
    assert f"{sans_checks['encoded_characters']:,}" in sans and 'GenZui Serif' in sans
    assert 'href="sans"' in home and 'GenZui Sans' in home
    # Each switch label loads its own family's subset, never the main webfont.
    for label in ('serif','sans'):
        assert re.search(rf'font-family:GenZuiLabel-{label};src:url\(assets/proof-[0-9a-f]+\.woff2\)', home), label
        assert re.search(rf'font-family:GenZuiLabel-{label};src:url\(assets/proof-[0-9a-f]+\.woff2\)', sans), label
    assert len(set(re.findall(r'GenZuiLabel-(?:serif|sans);src:url\((assets/proof-[0-9a-f]+\.woff2)\)', home)))==2
    for suffix in ('ttf','woff2'):
        for folder in ('downloads','sans-v'+sans_version):
            actual=hashlib.sha256((OUT/folder/(SANS_STEM+'.'+suffix)).read_bytes()).hexdigest()
            assert actual==sans_checks[suffix+'_sha256']
    with ZipFile(OUT/'downloads'/f'{SANS_STEM}-{sans_version}.zip') as z:
        assert z.testzip() is None
        assert hashlib.sha256(z.read(SANS_STEM+'.ttf')).hexdigest()==sans_checks['ttf_sha256']
        assert {'OFL.txt','NOTICE.txt','GenSeki-OFL.txt','NotoSansHentaigana-OFL.txt','FRB-OFL.txt','Unicode-LICENSE.txt'}<=set(z.namelist())
        assert json.loads(z.read('kana-coverage.json'))['coverage']['Script plus Script_Extensions']=={'total':763,'covered':763,'missing':[]}
        assert json.loads((OUT/'downloads/GenZuiSans-kana-coverage.json').read_text())==json.loads(z.read('kana-coverage.json'))
    sans_data=json.loads(next((OUT/'assets').glob('sans-characters-*.json')).read_text())
    assert sans_data['family']=='GenZui Sans' and sans_data['total']==sans_checks['encoded_characters']==len(sans_data['characters'])
    assert sans_data['historical']==329 and sans_data['counts']=={'jp':16732,'hentaigana':290,'genseki':21,'frb':15,'cjk':1,'genzui':11}
    assert 'sans-characters-' in sans and 'id="character-grid"' in sans and 'id="unicode-grid"' in sans
    assert 'HISTORICAL KANA · DRAWINGS' not in sans and 'Windows / macOS / Linux' in sans and 'Windows / macOS / Linux' in home
    assert (OUT/'genzui-sans.css').read_text()==f"@import url('/sans-v{sans_version}/genzui-sans.css');\n"
    assert '/sans-v*' in (OUT/'_headers').read_text() and f'{URL}/sans</loc>' in (OUT/'sitemap.xml').read_text()
    data=json.loads(next((OUT/'assets').glob('characters-*.json')).read_text())
    assert data['total']==17064+len(OKINAWAN_PUA) and len(data['characters'])==17064+len(OKINAWAN_PUA)
    assert data['historical']==329
    groups = {name: {c['cp'] for c in data['characters'] if c['group']==name}
              for name in ('han-numeral','tally-mark','ideographic-description')}
    assert len(groups['han-numeral'])==80 and {0x5344,0x5EFF,0x5345} <= groups['han-numeral']
    assert groups['tally-mark']==set(range(0x1D372,0x1D377))
    assert groups['ideographic-description']==set(range(0x2FF0,0x3000))|{0x31EF}
    assert 'Honkoku additions' not in home and 'sample=honkoku' not in home
    assert sum(c['source']=='genzui' for c in data['characters'])==32+len(OKINAWAN_PUA)
    assert {c['cp'] for c in data['characters'] if c['group']=='okinawan'} == set(OKINAWAN_PUA)
    assert json.loads((OUT/'downloads/okinawan-mappings.json').read_text()) == OKINAWAN_DATA
    assert 'id="okinawan-source"' in home and 'id="okinawan-output"' in home
    report={'version':VERSION,'font_sha256':checks['ttf_sha256'],
            'sans_version':sans_version,'sans_font_sha256':sans_checks['ttf_sha256'],'local_links_checked':count,
            'public_gallery_forms':21,'release_files_checked':len(manifest['files']),
            'inventory_collections':{name:len(points) for name,points in groups.items()},
            'extended_kana_characters':data['historical'],
            'font_bytes_unchanged':True,'status':'passed'}
    (ROOT/'research/release-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
