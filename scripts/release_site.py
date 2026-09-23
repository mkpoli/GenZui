"""Build the public GenZui site from the checked release and specimen sources."""
import base64
import hashlib
import html
import json
import re
import runpy
import shutil
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from design_gallery import build_gallery
from release_copy import FORM_DESCRIPTIONS
from serif import OUT as FONT_OUT, STEM, VERSION
from social_card import build_card
from sans_card import build_card as build_sans_card
from font_chunks import build as build_chunks
from sans_site import OUT as SANS_OUT, STEM as SANS_STEM, build_page as build_sans_page, checked as sans_checked
from sources import ROOT

OUT = ROOT/'build/release'
URL = 'https://genzui.mkpo.li'
DESCRIPTION = 'GenZui / 源萃: GenZui Serif (源萃明朝) and GenZui Sans (源萃ゴシック), Noto derivatives with 286 hentaigana, historical kana, Unicode 18 kana additions, Minnan tone letters and an Okinawan input tool.'
SERIF_DESCRIPTION = 'GenZui Serif / 源萃明朝: a Noto Serif JP derivative with 286 hentaigana, historical kana, Unicode 18 kana additions, Minnan tone letters and an Okinawan input tool.'
SITE_NAME = 'GenZui / 源萃 — Serif & Sans'
SANS_DESCRIPTION = 'GenZui Sans / 源萃ゴシック: a Noto Sans JP derivative with 286 hentaigana, historical kana, Unicode 18 kana additions and Minnan tone letters.'


def metadata(page, route, title, description, image_alt, image='genzui-social.png', site_name=SITE_NAME):
    page = re.sub(r'<meta name="description"[^>]*>', '', page)
    route = route.removesuffix('.html')
    for name in ('gallery', 'minnan', 'sans', 'serif'):
        page = page.replace(f'href="{name}.html', f'href="{name}')
    page = page.replace('href="index.html', 'href="./')
    tags = [f'<link rel="canonical" href="{URL}{route}">',
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
            f'<meta name="description" content="{html.escape(description, quote=True)}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{html.escape(site_name, quote=True)}">',
            f'<meta property="og:url" content="{URL}{route}">',
            f'<meta property="og:title" content="{html.escape(title, quote=True)}">',
            f'<meta property="og:description" content="{html.escape(description, quote=True)}">',
            f'<meta property="og:image" content="{URL}/media/{image}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            f'<meta property="og:image:alt" content="{html.escape(image_alt, quote=True)}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:image" content="{URL}/media/{image}">',
            f'<meta name="twitter:image:alt" content="{html.escape(image_alt, quote=True)}">']
    page = re.sub(r'<link rel="icon"[^>]*>', '', page)
    page = page.replace('</body>', '<script src="assets/proof-font.js"></script></body>')
    return page.replace('</head>', '\n'.join(tags)+'\n</head>')


def external_fonts(page):
    def save(match):
        raw = base64.b64decode(match[1])
        name = 'proof-'+hashlib.sha256(raw).hexdigest()[:16]+'.woff2'
        (OUT/'assets'/name).write_bytes(raw)
        return 'url(assets/'+name+')'
    return re.sub(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', save, page)


def external_data(page, prefix, descriptions=None):
    """Move the inline inventory JSON to a hashed asset the page fetches."""
    match = re.search(r'<script id="font-data" type="application/json"[^>]*>(.*?)</script>', page, re.S)
    data = json.loads(match[1])
    for item in data['characters']:
        if descriptions and item['cp'] in descriptions:
            item['description'] = descriptions[item['cp']]
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    name = prefix+'-'+hashlib.sha256(raw).hexdigest()[:16]+'.json'
    (OUT/'assets'/name).write_bytes(raw)
    family=re.search(r'data-family="([^"]*)"', match.group(0))
    attribute=f' data-family="{family[1]}"' if family else ''
    return page[:match.start()]+f'<script id="font-data" type="application/json"{attribute} data-src="assets/{name}"></script>'+page[match.end():]


def build():
    checks = json.loads((FONT_OUT/'checks.json').read_text())
    assert checks['status'] == 'passed'
    archive = ROOT/'dist'/f'{STEM}-{VERSION}.zip'
    versioned = ROOT/'releases'/('v'+VERSION)
    versioned.mkdir(parents=True, exist_ok=True)
    # Versioned release assets are immutable and survive subsequent builds.
    for source in [FONT_OUT/(STEM+'.ttf'), FONT_OUT/(STEM+'.woff2'), archive]:
        data = source.read_bytes()
        if source.suffix != '.zip':
            assert hashlib.sha256(data).hexdigest() == checks[source.suffix[1:]+'_sha256']
        target = versioned/source.name
        if target.exists():
            assert target.read_bytes() == data, 'Bump the font version before replacing a published asset.'
        else:
            target.write_bytes(data)
    css = ("@font-face {\n  font-family: 'GenZui Serif';\n"
           f"  src: url('./{STEM}.woff2') format('woff2');\n"
           "  font-weight: 400;\n  font-style: normal;\n  font-display: swap;\n}\n")
    css_path = versioned/'genzui.css'
    if css_path.exists():
        assert css_path.read_text() == css, 'Versioned CSS is immutable.'
    else:
        css_path.write_text(css)
    sans_version, sans_checks, sans_archive = sans_checked()
    sans_versioned = ROOT/'releases'/('sans-v'+sans_version)
    sans_versioned.mkdir(parents=True, exist_ok=True)
    for source in [SANS_OUT/(SANS_STEM+'.ttf'), SANS_OUT/(SANS_STEM+'.woff2'), sans_archive]:
        data = source.read_bytes()
        if source.suffix != '.zip':
            assert hashlib.sha256(data).hexdigest() == sans_checks[source.suffix[1:]+'_sha256']
        target = sans_versioned/source.name
        if target.exists():
            assert target.read_bytes() == data, 'Bump the Sans version before replacing a published asset.'
        else:
            target.write_bytes(data)
    sans_css = ("@font-face {\n  font-family: 'GenZui Sans';\n"
                f"  src: url('./{SANS_STEM}.woff2') format('woff2');\n"
                "  font-weight: 400;\n  font-style: normal;\n  font-display: swap;\n}\n")
    sans_css_path = sans_versioned/'genzui-sans.css'
    if sans_css_path.exists():
        assert sans_css_path.read_text() == sans_css, 'Versioned CSS is immutable.'
    else:
        sans_css_path.write_text(sans_css)
    runpy.run_path(str(ROOT/'scripts/site.py'))['build']()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT/'assets').mkdir(parents=True)
    (OUT/'downloads').mkdir()
    guard = (ROOT/'site/proof-font.js').read_bytes()
    guard_name = 'proof-font-'+hashlib.sha256(guard).hexdigest()[:16]+'.js'
    (OUT/'assets'/guard_name).write_bytes(guard)
    home_alt = build_card(OUT/'media')
    for release in (ROOT/'releases').iterdir():
        if release.is_dir() and re.fullmatch(r'(sans-)?v[0-9.]+', release.name):shutil.copytree(release, OUT/release.name)
    for source in (ROOT/'build/site/downloads').iterdir():
        if source.is_file():shutil.copy2(source, OUT/'downloads'/source.name)
    shutil.copytree(ROOT/'build/site/browser', OUT/'browser')
    (OUT/'genzui.css').write_text(f"@import url('/v{VERSION}/genzui.css');\n")
    (OUT/'genzui-sans.css').write_text(f"@import url('/sans-v{sans_version}/genzui-sans.css');\n")

    # Each family is served in unicode-range chunks so a page fetches only the
    # slices its text uses; the versioned /v*/ webfonts stay whole for other sites.
    site_text = set()
    for source in (ROOT/'build/site').glob('*.html'):
        site_text.update(ord(c) for c in re.sub(r'<[^>]+>|&[#a-zA-Z0-9]+;', ' ', source.read_text()))
    serif_css, serif_chunks = build_chunks(FONT_OUT/(STEM+'.ttf'), 'GenZui', STEM, OUT/'assets', site_text)
    sans_css, sans_chunks = build_chunks(SANS_OUT/(SANS_STEM+'.ttf'), 'GenZui', SANS_STEM, OUT/'assets', site_text)
    preload = lambda files: ''.join(f'<link rel="preload" as="font" type="font/woff2" crossorigin href="assets/{f}">' for f in files if '-text-' in f)
    # The landing declares a second family name for the Sans face.
    landing_serif_css = serif_css
    landing_sans_css = sans_css.replace('font-family:GenZui;', 'font-family:GenZuiSans;')
    sans_serif_css = serif_css.replace('font-family:GenZui;', 'font-family:GenZuiSerif;').replace('font-display:block', 'font-display:swap')
    page = (ROOT/'build/site/serif.html').read_text()
    page = re.sub(r"@font-face \{font-family:GenZui;src:url\(data:font/woff2;base64,[A-Za-z0-9+/=]+\)[^}]*\}",
                  lambda m: serif_css, page, count=1)
    page = page.replace('</head>', preload(serif_chunks)+'</head>')
    page = external_fonts(page)
    page = external_data(page, 'characters', FORM_DESCRIPTIONS)
    page = page.replace('<h3>A development build</h3>', '<h3>Historical letterforms</h3>')
    page = page.replace('The constructed outlines remain provisional.', 'GenZui supplies historical letterforms and transcription symbols using Noto components and original drawing.')
    page = page.replace('Regular · {{VERSION}} development build', 'Regular · {{VERSION}}')
    page = page.replace(f'{VERSION} development build', VERSION)
    page = page.replace('Review GenZui’s constructions', 'See GenZui’s constructions')
    web = (f'<details class="webfont-usage"><summary>Use GenZui on your website</summary>'
           f'<p>Load the <a href="v{VERSION}/genzui.css">version {VERSION} stylesheet</a>, then set the font family:</p>'
           f'<pre><code>&lt;link rel="stylesheet" href="{URL}/v{VERSION}/genzui.css"&gt;\n\n'
           'body {\n  font-family: "GenZui Serif", serif;\n}</code></pre></details>')
    page = page.replace('<!-- webfont-usage -->', web)
    structured = {'@context':'https://schema.org', '@type':'WebSite',
                  'name':'GenZui / 源萃', 'url':URL+'/', 'description':DESCRIPTION,
                  'author':{'@type':'Person','name':'まくぽり / mkpoli','url':'https://mkpo.li/'}}
    page = page.replace('</head>', '<script type="application/ld+json">'+json.dumps(structured,ensure_ascii=False)+'</script></head>')
    (OUT/'serif.html').write_text(metadata(page, '/serif', '源萃明朝 — GenZui Serif', SERIF_DESCRIPTION, home_alt))
    landing = (ROOT/'build/site/index.html').read_text()
    landing = re.sub(r"@font-face \{font-family:GenZui;src:url\(data:font/woff2;base64,[A-Za-z0-9+/=]+\)[^}]*\}",
                     lambda m: landing_serif_css, landing, count=1)
    landing = re.sub(r"@font-face \{font-family:GenZuiSans;src:url\(data:font/woff2;base64,[A-Za-z0-9+/=]+\)[^}]*\}",
                     lambda m: landing_sans_css, landing, count=1)
    landing = landing.replace('</head>', preload(serif_chunks)+preload(sans_chunks)+'</head>')
    landing = external_fonts(landing)
    landing = landing.replace('</head>', '<script type="application/ld+json">'+json.dumps(structured,ensure_ascii=False)+'</script></head>')
    (OUT/'index.html').write_text(metadata(landing, '/', '源萃 — GenZui Serif / GenZui Sans', DESCRIPTION, home_alt))
    sans_web = (f'<details class="webfont-usage"><summary>Use GenZui Sans on your website</summary>'
                f'<p>Load the <a href="sans-v{sans_version}/genzui-sans.css">version {sans_version} stylesheet</a>, then set the font family:</p>'
                f'<pre><code>&lt;link rel="stylesheet" href="{URL}/sans-v{sans_version}/genzui-sans.css"&gt;\n\n'
                'body {\n  font-family: "GenZui Sans", sans-serif;\n}</code></pre></details>')
    sans_page = build_sans_page('SANS_CHUNKS', 'SERIF_CHUNKS', sans_web)
    sans_page = re.sub(r"@font-face \{font-family:GenZui;src:url\(SANS_CHUNKS\)[^}]*\}", lambda m: sans_css, sans_page, count=1)
    sans_page = re.sub(r"@font-face \{font-family:GenZuiSerif;src:url\(SERIF_CHUNKS\)[^}]*\}",
                       lambda m: sans_serif_css, sans_page, count=1)
    sans_page = sans_page.replace('</head>', preload(sans_chunks)+'</head>')
    sans_page = external_data(sans_page, 'sans-characters')
    sans_alt = build_sans_card(OUT/'media')
    sans_structured = {'@context':'https://schema.org', '@type':'WebSite',
                       'name':'GenZui Sans / 源萃ゴシック', 'url':URL+'/sans', 'description':SANS_DESCRIPTION,
                       'author':{'@type':'Person','name':'まくぽり / mkpoli','url':'https://mkpo.li/'}}
    sans_page = sans_page.replace('</head>', '<script type="application/ld+json">'+json.dumps(sans_structured,ensure_ascii=False)+'</script></head>')
    (OUT/'sans.html').write_text(metadata(external_fonts(sans_page), '/sans', '源萃ゴシック — GenZui Sans', SANS_DESCRIPTION,
                                          sans_alt, image='genzui-sans-social.png'))
    for route, content, title, description in [
        ('gallery.html', build_gallery(public=True), 'GenZui Serif — Design gallery',
         'Twenty-one GenZui historical kana constructions, with horizontal and vertical samples, stroke references and two WU forms.'),
        ('minnan.html', (ROOT/'build/site/minnan.html').read_text(), 'Minnan kana & archaic WU — GenZui Serif',
         'Minnan tone letters, combining marks and two archaic WU forms in GenZui Serif.')]:
        (OUT/route).write_text(metadata(external_fonts(content), '/'+route, title, description, home_alt))
    font = TTFont(FONT_OUT/(STEM+'.ttf'))
    pen = SVGPathPen(font.getGlyphSet());font.getGlyphSet()[font.getBestCmap()[0x1B123]].draw(pen)
    (OUT/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><rect width="1000" height="1000" rx="170" fill="#214e3c"/><path fill="#f7f8f2" transform="translate(80 804) scale(.84 -.84)" d="'+pen.getCommands()+'"/></svg>')
    (OUT/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found — GenZui</title><style>body{max-width:36em;margin:15vh auto;padding:24px;background:#f7f8f2;color:#25382e;font:18px/1.6 system-ui}a{color:#214e3c}</style><h1>Page not found.</h1><p><a href="/">Return to GenZui</a></p></html>')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+URL+'/sitemap.xml\n')
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+URL+r+'</loc></url>' for r in ['/', '/serif', '/sans', '/gallery', '/minnan'])+'</urlset>')
    (OUT/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/\n  Cache-Control: public, max-age=300\n/*.html\n  Cache-Control: public, max-age=300\n/serif\n  Cache-Control: public, max-age=300\n/sans\n  Cache-Control: public, max-age=300\n/gallery\n  Cache-Control: public, max-age=300\n/minnan\n  Cache-Control: public, max-age=300\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/v*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=31536000, immutable\n/sans-v*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=31536000, immutable\n/downloads/*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=3600\n/media/*\n  Cache-Control: public, max-age=86400\n/genzui.css\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=300\n/genzui-sans.css\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=300\n')
    (OUT/'_redirects').write_text('/index.html / 301\n')
    for name in ['announcement-ja', 'announcement-en', 'announcement-sans-ja', 'announcement-sans-en']:
        shutil.copyfile(ROOT/'release'/(name+'.txt'), OUT/(name+'.txt'))
    for name in ['index.html','serif.html','sans.html','gallery.html','minnan.html']:
        p=OUT/name
        p.write_text(p.read_text().replace('assets/proof-font.js','assets/'+guard_name))
    hashes = {str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.rglob('*')) if p.is_file()}
    (OUT/'release.json').write_text(json.dumps({'version':VERSION,'font_sha256':checks['ttf_sha256'],'sans_version':sans_version,'sans_font_sha256':sans_checks['ttf_sha256'],'files':hashes},indent=2)+'\n')
    print(f'Public GenZui {VERSION}: {len(hashes)} assets; {len((OUT/"index.html").read_bytes()):,}-byte landing page.')


if __name__ == '__main__':build()
