"""Verify WU's default/alternate selection, shape, and mark attachment."""
from PIL import Image, ImageDraw, ImageFont
from check_refinements import components
from serif_forms import wu_alternate


def check_variants(path, font, engine, shape, boxes):
    default = font.getBestCmap()[0x1B11F]
    alternate = wu_alternate(font)
    default_id, alt_id = map(font.getGlyphID, (default, alternate))
    feature = next(r.Feature for r in font['GSUB'].table.FeatureList.FeatureRecord if r.FeatureTag == 'ss01')
    assert font['name'].getDebugName(feature.FeatureParams.UINameID) == 'Hooked WU'
    assert font['hmtx'][default][0] == font['hmtx'][alternate][0] == 1000
    assert font['vmtx'][default][0] == font['vmtx'][alternate][0] == 1000
    # The top of each right-hand contour is HO's 729-unit bar. Its stem
    # must not add a new projecting head. The separate left contour is taller.
    for name in (default, alternate):
        coords, ends, flags = font['glyf'][name].getCoordinates(font['glyf'])
        contours, start = [], 0
        for end in ends:
            contours.append(list(coords[start:end+1])); start = end+1
        right = [c for c in contours if min(p[0] for p in c)>400]
        assert len(right) == 1 and max(p[1] for p in right[0]) == 729, name
    assert font['glyf'][default].yMin == -63
    cases = 0
    for script in ('Hira','Kana','Latn','Zzzz','Hani'):
        for direction in ('ltr','ttb'):
            for enabled in (False, True):
                features = {'ss01': enabled}
                shaped = shape(engine, '𛄟', direction, features, script)
                assert shaped[0][0] == (alt_id if enabled else default_id)
                assert shaped[0][1:3] == ((1000,0) if direction == 'ltr' else (0,-1000))
                for mark in ('\u3099','\u309a'):
                    marked = shape(engine, '𛄟'+mark, direction, features, script)
                    assert len(marked)==2 and marked[0][0]==shaped[0][0]
                    assert marked[1][1:3] == (0,0)
                    base, accent = boxes(font, marked)
                    assert (accent[1]>=base[3]+18 if direction=='ltr' else accent[0]>=base[2]+18)
                    cases += 1
    # Turning the stylistic set on must affect only WU in the full repertoire.
    text = ''.join(map(chr, sorted(font.getBestCmap())))
    for direction in ('ltr','ttb'):
        before=shape(engine,text,direction,{'ss01':False})
        after=shape(engine,text,direction,{'ss01':True})
        changes=[(a,b) for a,b in zip(before,after) if a!=b]
        assert len(before)==len(after) and len(changes)==1
        assert changes[0][0][0]==default_id and changes[0][1][0]==alt_id
        assert changes[0][0][1:] == changes[0][1][1:]
    raster=[]
    for size in (32,48,128):
        face=ImageFont.truetype(str(path),size)
        for enabled in (False,True):
            image=Image.new('L',(size+40,size+40))
            ImageDraw.Draw(image).text((20,size*.88+20),'𛄟',font=face,anchor='ls',fill=255,
                                      features=['ss01' if enabled else '-ss01'])
            assert components(image)==2,(size,enabled)
            raster.append({'size_px':size,'ss01':enabled,'components':2})
    return {'feature':'ss01','ui_name':'Hooked WU','default':'curved',
            'alternate':'hooked','right_contour_top_units':729,
            'mark_cases':cases,'only_wu_changes_in_full_repertoire':True,
            'raster_connectivity':raster,'status':'passed'}
