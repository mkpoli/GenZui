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
from sans_site import OUT as SANS_OUT, STEM as SANS_STEM, build_page as build_sans_page, checked as sans_checked
from sources import ROOT

OUT = ROOT/'build/release'
URL = 'https://genzui.mkpo.li'
DESCRIPTION = 'GenZui Serif / 源萃明朝: a Noto Serif JP derivative with 286 hentaigana, historical kana, Unicode 18 kana additions, Minnan tone letters and an Okinawan input tool.'
SANS_DESCRIPTION = 'GenZui Sans / 源萃ゴシック: a Noto Sans JP derivative with 286 hentaigana, historical kana, Unicode 18 kana additions and Minnan tone letters.'


def metadata(page, route, title, description, image='genzui-social.png', image_alt=None, site_name='GenZui Serif / 源萃明朝'):
    page = re.sub(r'<meta name="description"[^>]*>', '', page)
    route = route.removesuffix('.html')
    for name in ('gallery', 'minnan', 'sans'):
        page = page.replace(f'href="{name}.html', f'href="{name}')
    page = page.replace('href="index.html', 'href="./')
    image_alt = image_alt or '源萃明朝 / GenZui Serif. Six historical kana in the released font: KOTO, TOKI, TOMO, TOTE, alternate NE and alternate WI.'
    tags = [f'<link rel="canonical" href="{URL}{route}">',
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
            f'<meta name="description" content="{html.escape(description, quote=True)}">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{site_name}">',
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
    for release in (ROOT/'releases').iterdir():
        if release.is_dir() and re.fullmatch(r'(sans-)?v[0-9.]+', release.name):shutil.copytree(release, OUT/release.name)
    for source in (ROOT/'build/site/downloads').iterdir():
        if source.is_file():shutil.copy2(source, OUT/'downloads'/source.name)
    shutil.copytree(ROOT/'build/site/browser', OUT/'browser')
    (OUT/'genzui.css').write_text(f"@import url('/v{VERSION}/genzui.css');\n")
    (OUT/'genzui-sans.css').write_text(f"@import url('/sans-v{sans_version}/genzui-sans.css');\n")

    page = (ROOT/'build/site/index.html').read_text()
    page = re.sub(r'url\(data:font/woff2;base64,[A-Za-z0-9+/=]+\)',
                  f'url(v{VERSION}/{STEM}.woff2)', page)
    match = re.search(r'<script id="font-data" type="application/json">(.*?)</script>', page, re.S)
    data = json.loads(match[1])
    for item in data['characters']:
        if item['cp'] in FORM_DESCRIPTIONS:
            item['description'] = FORM_DESCRIPTIONS[item['cp']]
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    name = 'characters-'+hashlib.sha256(raw).hexdigest()[:16]+'.json'
    (OUT/'assets'/name).write_bytes(raw)
    page = page[:match.start()]+f'<script id="font-data" type="application/json" data-src="assets/{name}"></script>'+page[match.end():]
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
                  'name':'GenZui Serif / 源萃明朝', 'url':URL+'/', 'description':DESCRIPTION,
                  'author':{'@type':'Person','name':'まくぽり / mkpoli','url':'https://mkpo.li/'}}
    page = page.replace('</head>', '<script type="application/ld+json">'+json.dumps(structured,ensure_ascii=False)+'</script></head>')
    (OUT/'index.html').write_text(metadata(page, '/', '源萃明朝 — GenZui Serif', DESCRIPTION))
    sans_web = (f'<details class="webfont-usage"><summary>Use GenZui Sans on your website</summary>'
                f'<p>Load the <a href="sans-v{sans_version}/genzui-sans.css">version {sans_version} stylesheet</a>, then set the font family:</p>'
                f'<pre><code>&lt;link rel="stylesheet" href="{URL}/sans-v{sans_version}/genzui-sans.css"&gt;\n\n'
                'body {\n  font-family: "GenZui Sans", sans-serif;\n}</code></pre></details>')
    sans_page = build_sans_page(f'sans-v{sans_version}/{SANS_STEM}.woff2', f'v{VERSION}/{STEM}.woff2', sans_web)
    sans_alt = build_sans_card(OUT/'media')
    sans_structured = {'@context':'https://schema.org', '@type':'WebSite',
                       'name':'GenZui Sans / 源萃ゴシック', 'url':URL+'/sans', 'description':SANS_DESCRIPTION,
                       'author':{'@type':'Person','name':'まくぽり / mkpoli','url':'https://mkpo.li/'}}
    sans_page = sans_page.replace('</head>', '<script type="application/ld+json">'+json.dumps(sans_structured,ensure_ascii=False)+'</script></head>')
    (OUT/'sans.html').write_text(metadata(sans_page, '/sans', '源萃ゴシック — GenZui Sans', SANS_DESCRIPTION,
                                          image='genzui-sans-social.png', image_alt=sans_alt, site_name='GenZui Sans / 源萃ゴシック'))
    for route, content, title, description in [
        ('gallery.html', build_gallery(public=True), 'GenZui Serif — Design gallery',
         'Twenty-one GenZui historical kana constructions, with horizontal and vertical samples, stroke references and two WU forms.'),
        ('minnan.html', (ROOT/'build/site/minnan.html').read_text(), 'Minnan kana & archaic WU — GenZui Serif',
         'Minnan tone letters, combining marks and two archaic WU forms in GenZui Serif.')]:
        (OUT/route).write_text(metadata(external_fonts(content), '/'+route, title, description))
    font = TTFont(FONT_OUT/(STEM+'.ttf'))
    pen = SVGPathPen(font.getGlyphSet());font.getGlyphSet()[font.getBestCmap()[0x1B123]].draw(pen)
    (OUT/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><rect width="1000" height="1000" rx="170" fill="#214e3c"/><path fill="#f7f8f2" transform="translate(80 804) scale(.84 -.84)" d="'+pen.getCommands()+'"/></svg>')
    (OUT/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found — GenZui Serif</title><style>body{max-width:36em;margin:15vh auto;padding:24px;background:#f7f8f2;color:#25382e;font:18px/1.6 system-ui}a{color:#214e3c}</style><h1>Page not found.</h1><p><a href="/">Return to GenZui Serif</a></p></html>')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+URL+'/sitemap.xml\n')
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+URL+r+'</loc></url>' for r in ['/', '/sans', '/gallery', '/minnan'])+'</urlset>')
    (OUT/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/\n  Cache-Control: public, max-age=300\n/*.html\n  Cache-Control: public, max-age=300\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/v*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=31536000, immutable\n/sans-v*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=31536000, immutable\n/downloads/*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=3600\n/media/*\n  Cache-Control: public, max-age=86400\n/genzui.css\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=300\n/genzui-sans.css\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=300\n')
    (OUT/'_redirects').write_text('/index.html / 301\n')
    build_card(OUT/'media')
    for name in ['announcement-ja', 'announcement-en', 'announcement-sans-ja', 'announcement-sans-en']:
        shutil.copyfile(ROOT/'release'/(name+'.txt'), OUT/(name+'.txt'))
    for name in ['index.html','sans.html','gallery.html','minnan.html']:
        p=OUT/name
        p.write_text(p.read_text().replace('assets/proof-font.js','assets/'+guard_name))
    hashes = {str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.rglob('*')) if p.is_file()}
    (OUT/'release.json').write_text(json.dumps({'version':VERSION,'font_sha256':checks['ttf_sha256'],'sans_version':sans_version,'sans_font_sha256':sans_checks['ttf_sha256'],'files':hashes},indent=2)+'\n')
    print(f'Public GenZui {VERSION}: {len(hashes)} assets; {len((OUT/"index.html").read_bytes()):,}-byte home page.')


if __name__ == '__main__':build()
