"""Render the raised-katakana follow-up card from GenZui Serif Okinawan."""
import hashlib
import html
import json
from PIL import Image,ImageDraw,ImageFont,features
from fontTools.ttLib import TTFont
from sources import ROOT
from serif import OUT as FULL,VERSION
from okinawan import ENTRIES
from okinawan_subset import OUT as FONT_OUT,PREFIX
from okinawan_release_proof import OUT as PROOF_OUT

OUT=PROOF_OUT/'sns-raised'
SOURCE='https://www.pref.okinawa.lg.jp/_res/projects/default_project/_page_/001/009/625/02_shimakutubahyouki.pdf'
PROPOSAL='https://www.unicode.org/L2/L2023/23118-ryukyu-kana.pdf'
ENTRIES_RAISED=[e for e in ENTRIES if e['system']=='prefecture']
# Attested notation examples, not invented vocabulary: proposal Table 1.
FOLLOWERS=['ア','イ','ウ','エ','オ','ワ','ア','ン']

def build():
    assert features.check('raqm') and len(ENTRIES_RAISED)==8
    OUT.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(2400,1260),'#06241a');d=ImageDraw.Draw(im)
    fonts={s:FONT_OUT/f'{PREFIX}-{s}.ttf' for s in ('Regular','Bold')}
    for path in fonts.values():
        cmap=TTFont(path).getBestCmap()
        assert {int(e['output'][0],16) for e in ENTRIES_RAISED}|set(map(ord,''.join(FOLLOWERS))) <= set(cmap)
    for x in range(0,1200,32):d.line((x*2,0,x*2,1260),fill='#0a2d21',width=2)
    for y in range(0,630,32):d.line((0,y*2,2400,y*2),fill='#0a2d21',width=2)
    def text(x,y,value,size,style='Regular',color='#f4f7f1',ui=False,latin=False,anchor='ls'):
        face='DejaVuSans.ttf' if latin else str(FULL/f'GenZuiSerif-{style}.ttf' if ui else fonts[style])
        font=ImageFont.truetype(face,round(size*2),layout_engine=ImageFont.Layout.RAQM)
        bounds=d.textbbox((x*2,y*2),value,font=font,anchor=anchor)
        assert 0<=bounds[0]<bounds[2]<=2400 and 0<=bounds[1]<bounds[3]<=1260,(value,bounds)
        d.text((x*2,y*2),value,font=font,anchor=anchor,fill=color)
        return bounds
    text(60,63,'源萃明朝',34,'Bold',ui=True)
    text(240,61,'上付きカタカナ',20,ui=True,color='#86b09a')
    text(1140,60,VERSION,14,latin=True,color='#86b09a',anchor='rs')
    for style,left,fill,ink,muted in [('Regular',60,'#f4f7f1','#1f634d','#5f7d6e'),('Bold',615,'#0b3326','#f4f7f1','#86b09a')]:
        right=left+525
        d.rectangle((left*2,192,right*2,1140),fill=fill,outline='#1f634d' if style=='Bold' else None,width=2)
        for x,y,dx,dy in [(left-6,90,1,1),(right+6,90,-1,1),(left-6,576,1,-1),(right+6,576,-1,-1)]:
            d.line((x*2,y*2,(x+16*dx)*2,y*2),fill='#3fae84',width=4);d.line((x*2,y*2,x*2,(y+16*dy)*2),fill='#3fae84',width=4)
        text(left+28,128,style.upper(),12,color=muted,latin=True)
        for i,e in enumerate(ENTRIES_RAISED):
            ch=chr(int(e['output'][0],16));col,row=i%4,i//4
            text(left+84+col*116,246+row*102,ch,112,style,ink,anchor='ms')
        d.line(((left+28)*2,744,(right-28)*2,744),fill='#cbd8cb' if style=='Regular' else '#1f634d',width=2)
        for i,(e,following) in enumerate(zip(ENTRIES_RAISED,FOLLOWERS)):
            value=chr(int(e['output'][0],16))+following;col,row=i%4,i//4
            bounds=text(left+40+col*116,453+row*78,value,54,style,ink)
            assert left*2<bounds[0]<bounds[2]<right*2
    text(60,610,'genzui.mkpo.li',16,color='#86b09a',latin=True)
    name=f'genzui-{VERSION}-raised-katakana.png';im.save(OUT/name,optimize=True)
    alt='源萃明朝の上付きカタカナ8字。ア・イ・ウ・エ・オ・ツ・フ・ンを左にRegular、右にBoldで配置。下段に通常のカタカナと組み合わせた表記例。'
    manifest=dict(version=VERSION,family='GenZui Serif Okinawan',size=[2400,1260],source=SOURCE,notation_source=PROPOSAL,
                  note='Eight notation combinations from the proposal table; these are sound-notation examples, not sentences. PUA mappings follow the repository registry.',
                  forms=[dict(label=e['label'],codepoint=e['output'][0],example=chr(int(e['output'][0],16))+f) for e,f in zip(ENTRIES_RAISED,FOLLOWERS)],
                  font_sha256={s:hashlib.sha256(p.read_bytes()).hexdigest() for s,p in fonts.items()},
                  image=dict(file=name,sha256=hashlib.sha256((OUT/name).read_bytes()).hexdigest(),alt_ja=alt))
    (OUT/'specimens.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(OUT/'alt-ja.txt').write_text(alt+'\n')
    caption=(ROOT/'release/announcement-raised-0.118-ja.txt').read_text();(OUT/'announcement-ja.txt').write_text(caption)
    page=f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>源萃明朝 · 上付きカタカナ</title><style>body{{margin:0;background:#f7f8f2;color:#25382e;font:16px/1.7 system-ui}}main{{max-width:1240px;margin:auto;padding:30px}}img{{width:100%;display:block}}a{{color:#214e3c}}textarea{{width:100%;box-sizing:border-box;min-height:240px;padding:16px;font:inherit}}</style><main><a href="../sns/">新沖縄文字の投稿</a><h1>源萃明朝 · 上付きカタカナ</h1><a href="{name}"><img src="{name}" alt="{html.escape(alt)}"></a><p><a href="{name}" download>PNGを保存</a> · 2400×1260px</p><textarea aria-label="SNS投稿文">{html.escape(caption)}</textarea><p>表記の出典：<a href="{SOURCE}">沖縄県「しまくとぅば」の表記について</a>。下段は<a href="{PROPOSAL}">上付きカタカナの符号化提案</a>の表記例。フォントの私用領域の対応は<a href="/genzui-okinawan-subset/okinawan-mappings.json">文字コード表</a>に記載。</p><a href="alt-ja.txt">代替テキスト</a></main></html>'''
    (OUT/'index.html').write_text(page)
    print('Raised-katakana SNS image, Japanese post, source record and alt text prepared.')

if __name__=='__main__':build()
