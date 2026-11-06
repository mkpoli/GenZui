"""The site select that the logo opens on every public page."""
import re

from sources import ROOT
from sponsor_site import SITE, hashed

FILES = ('site-select.css', 'site-select.js', 'brand/kureedo.svg', 'brand/genzui.svg')
ASSETS = {name: 'assets/'+hashed(name) for name in FILES}


def write_assets(directory):
    """Copy the stylesheet, script and the two logos under their hashed names."""
    for name in FILES:
        (directory/ASSETS[name].removeprefix('assets/')).write_bytes((SITE/name).read_bytes())


def inject(page):
    """Link the stylesheet and the deferred script; the script reads the logos from its data attributes."""
    assert 'data-site-select=' in page, 'No logo to turn into the site select.'
    head = page.index('</head>')
    tags = (f'<link rel="stylesheet" href="{ASSETS["site-select.css"]}">'
            f'<script src="{ASSETS["site-select.js"]}" defer data-kureedo-logo="{ASSETS["brand/kureedo.svg"]}" '
            f'data-genzui-logo="{ASSETS["brand/genzui.svg"]}"></script>')
    return page[:head]+tags+page[head:]
