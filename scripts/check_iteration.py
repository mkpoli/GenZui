"""Compare the current outline iteration with its preserved gallery baseline."""
import hashlib
import json
import io
from PIL import Image, ImageDraw, ImageFont, ImageChops
import pathops
from fontTools.ttLib import TTFont
from check_refinements import mask, components, runs
from serif_forms import REVISION_0111, wu_alternate
from serif import contours, transform
from sources import ROOT


def check_iteration(path, font):
    folder = ROOT/'research/baselines'
    raw = folder/'GenZui-0.110-gallery.woff2'
    baseline = json.loads((folder/'gallery-0.110.json').read_text())
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == baseline['subset_woff2_sha256']
    before = TTFont(raw)
    changed = []
    for cp, name in before.getBestCmap().items():
        old = before['glyf'][name].getCoordinates(before['glyf'])
        new = font['glyf'][font.getBestCmap()[cp]].getCoordinates(font['glyf'])
        if old != new:
            changed.append(cp)
    assert set(changed) == set(REVISION_0111), [hex(cp) for cp in changed]
    assert (before['glyf'][wu_alternate(before)].getCoordinates(before['glyf']) !=
            font['glyf'][wu_alternate(font)].getCoordinates(font['glyf']))
    current_wu=font.getBestCmap()[0x1B11F]
    assert (before['glyf'][before.getBestCmap()[0x1B11F]].getCoordinates(before['glyf']) ==
            font['glyf'][current_wu].getCoordinates(font['glyf']))
    accepted=folder/'Koto-E-accepted.woff2'
    assert hashlib.sha256(accepted.read_bytes()).hexdigest() == json.loads((folder/'Koto-E-accepted.json').read_text())['sha256']
    e=TTFont(accepted)
    assert (e['glyf'][e.getBestCmap()[0x1B123]].getCoordinates(e['glyf']) ==
            font['glyf'][font.getBestCmap()[0x1B123]].getCoordinates(font['glyf']))
    assert not set(changed) & {0x1B124,0x1B125,0x1B126,0x2A708,0x2CF00,0x2CF02,0x2CEFF}
    def section(face, name, height):
        p=pathops.Path(); face.getGlyphSet()[name].draw(p.getPen())
        xs=[x for x in range(600,800) if p.contains((x,height))]
        return max(xs)-min(xs)+1, (min(xs)+max(xs))/2
    width,centre=section(font,wu_alternate(font),250)
    old_width,old_centre=section(before,wu_alternate(before),250)
    midwidth,midcentre=section(font,wu_alternate(font),350)
    old_midwidth,old_midcentre=section(before,wu_alternate(before),350)
    assert 55 <= width <= 65 and 55 <= midwidth <= 65, (width,midwidth)
    g=font['glyf'][wu_alternate(font)]
    assert -65 <= g.yMin <= -45, g.yMin
    def raster(face, cp, features=()):
        flavor=face.flavor; face.flavor=None
        raw=io.BytesIO();face.save(raw);face.flavor=flavor
        image=Image.new('L',(1040,1040))
        ImageDraw.Draw(image).text((20,900),chr(cp),font=ImageFont.truetype(io.BytesIO(raw.getvalue()),1000),anchor='ls',fill=255,features=list(features))
        return image
    nari_before=raster(before,0x2CF02);nari_after=raster(font,0x2CF02)
    assert ImageChops.difference(nari_before.crop((0,0,1040,620)),nari_after.crop((0,0,1040,620))).getbbox() is None
    kata_before=raster(before,0x2CEFF);kata_after=raster(font,0x2CEFF)
    assert ImageChops.difference(kata_before.crop((0,0,1040,400)),kata_after.crop((0,0,1040,400))).getbbox() is None
    def ink(im):return sum(im.getdata())/255
    lower_weight_ratio=ink(kata_after.crop((0,400,1040,1040)))/ink(kata_before.crop((0,400,1040,1040)))
    assert lower_weight_ratio == 1, lower_weight_ratio
    # Entry and lower body must retain substance at the same physical size.
    entry=sum(kata_after.getpixel((206,y))>=128 for y in range(430,560))
    body=sum(kata_after.getpixel((620,y))>=128 for y in range(720,940))
    assert entry >= 35 and 60 <= body <= 72,(entry,body)
    terminal=sum(nari_after.getpixel((870,y))>=128 for y in range(760,940))
    assert terminal >= 45, terminal
    # Preserve the existing bow above the revised heel connection.
    heights=(610,580,550,380,350)
    old_profile=[section(before,wu_alternate(before),y)[1] for y in heights]
    new_profile=[section(font,wu_alternate(font),y)[1] for y in heights]
    bow_deviation=max(abs(a-b) for a,b in zip(old_profile,new_profile))
    assert bow_deviation<=1,(old_profile,new_profile)
    # The shortened return sits farther right at reading height. The main
    # descent retains its weight; rounded joins are also inspected in proofs.
    def lower_extent(face):
        p=pathops.Path();face.getGlyphSet()[wu_alternate(face)].draw(p.getPen())
        xs=[x for x in range(400,800) if p.contains((x,60))]
        return min(xs),max(xs)
    old_extent=lower_extent(before);new_extent=lower_extent(font)
    assert new_extent[0]-old_extent[0] >= 75,(old_extent,new_extent)
    assert new_extent[1]-new_extent[0] < old_extent[1]-old_extent[0]
    joins=[]
    for cp,expected in [(0x2A708,1),(0x2CF00,1),(0x1B123,1),(0x2CEFF,2),(0x2CF02,1),(0x1B127,1),(0x1B128,1)]:
        for size in (24,32,40,48,64,128):
            actual=components(mask(path,cp,size))
            assert actual==expected,(hex(cp),size,actual)
            joins.append({'codepoint':f'U+{cp:X}','size_px':size,'components':actual})
    # Probe the top envelope around TOMO's T junction. Its stem must stay
    # below the native MO bar, allowing one design unit for curve rounding.
    bar=pathops.Path(); actual=pathops.Path()
    transform(transform(contours(font,0x30E2,[2]),(1,0,0,1,90,82)),(.92,0,0,.92,40,29.2)).replay(bar.getPen())
    contours(font,0x2A708).replay(actual.getPen())
    junction=[]
    for x in range(455,611,3):
        top=max(y for y in range(610,780) if bar.contains((x,y)))
        actual_top=max(y for y in range(610,780) if actual.contains((x,y)))
        assert abs(actual_top-top)<=1,(x,top,actual_top)
        junction.append(actual_top-top)
    return {'baseline':'0.110','changed_outlines':[f'U+{cp:X}' for cp in changed],
            'only_hooked_wu_alternate_changed':True,'all_encoded_outlines_unchanged':True,
            'koto_matches_accepted_E':True,'curved_wu_default_unchanged':True,
            'hooked_wu_stem_units':width,'hooked_wu_y_min':g.yMin,
            'stem_centres_high_to_low':{'heights':heights,'before':old_profile,'after':new_profile},
            'upper_bow_max_deviation_units':bow_deviation,
            'hook_extent_at_y60':{'before':old_extent,'after':new_extent},
            'katakana_nari_lower_ink_ratio':round(lower_weight_ratio,3),
            'tomo_top_envelope_samples':len(junction),'tomo_max_top_deviation_units':max(map(abs,junction)),
            'reading_size_connectivity':joins,'status':'passed'}
