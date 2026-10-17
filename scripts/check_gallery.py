"""Verify the gallery's embedded proof fonts and current WU variants."""
import base64
import hashlib
import io
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from check_refinements import components
from serif import OUT, STEM, VERSION
from serif_forms import wu_alternate, REVISION_0112
from check_serif import shaper, shape, serialized
from sources import ROOT


class Readings(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('meta','link','br','input','hr'):return
        classes=dict(attrs).get('class','').split()
        self.stack.append((tag,'reading' in classes))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                del self.stack[i:];break
    def handle_data(self, data):
        if any(reading for _,reading in self.stack):self.text.append(data)


def check():
    page=ROOT/'build/site/gallery.html'; source=page.read_text()
    embedded=re.findall(r'font-family:(GenZui|Previous);src:url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)',source)
    assert len(embedded)==2
    fonts={name:TTFont(io.BytesIO(base64.b64decode(raw))) for name,raw in embedded}
    current=fonts['GenZui']; full=TTFont(OUT/(STEM+'.ttf'))
    parser=Readings();parser.feed(source); points=set(map(ord,''.join(parser.text)))
    for name,font in fonts.items():
        assert points <= font.getBestCmap().keys(),(name,points-font.getBestCmap().keys())
        assert 'ss01' in [r.FeatureTag for r in font['GSUB'].table.FeatureList.FeatureRecord]
    for cp,name in current.getBestCmap().items():
        other=full.getBestCmap()[cp]
        assert current['glyf'][name].getCoordinates(current['glyf'])==full['glyf'][other].getCoordinates(full['glyf'])
        assert current['hmtx'][name]==full['hmtx'][other]
        assert current['vmtx'][name]==full['vmtx'][other]
    assert current['glyf'][wu_alternate(current)].getCoordinates(current['glyf'])==full['glyf'][wu_alternate(full)].getCoordinates(full['glyf'])
    old=fonts['Previous']
    changed=[cp for cp,name in old.getBestCmap().items() if old['glyf'][name].getCoordinates(old['glyf'])!=full['glyf'][full.getBestCmap()[cp]].getCoordinates(full['glyf'])]
    assert set(changed)==set(REVISION_0112)
    # The curved default is unchanged in both full and proof fonts.
    assert old['glyf'][old.getBestCmap()[0x1B11F]].getCoordinates(old['glyf'])==current['glyf'][current.getBestCmap()[0x1B11F]].getCoordinates(current['glyf'])
    # Minnan also demonstrates the two current forms, using the same feature.
    minnan=(ROOT/'build/site/minnan.html').read_text()
    raw=re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)',minnan)
    assert len(raw)==1
    minnanfont=TTFont(io.BytesIO(base64.b64decode(raw[0])))
    assert minnanfont['glyf'][wu_alternate(minnanfont)].getCoordinates(minnanfont['glyf'])==full['glyf'][wu_alternate(full)].getCoordinates(full['glyf'])
    assert 'Curved WU' not in minnan and 'Hooked WU' in minnan
    report={'version':VERSION,'ttf_sha256':hashlib.sha256((OUT/(STEM+'.ttf')).read_bytes()).hexdigest(),
            'gallery_sha256':hashlib.sha256(page.read_bytes()).hexdigest(),
            'all_reading_characters_covered':len(points),'proof_font_count':len(fonts),
            'proof_outlines_and_metrics_match_full_font':True,'curved_wu_default_unchanged':True,
            'minnan_preserves_hooked_alternate':True,
            'comparison_characters_unchanged':len(old.getBestCmap())-len(changed),'status':'passed'}
    (ROOT/'research/gallery-font-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':check()
