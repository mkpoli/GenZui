"""The Sponsor pill and dialog shared by every public page."""
import hashlib
import re

from sources import ROOT

SITE = ROOT/'site'
HEART = 'M12 21s-8.5-5.1-8.5-11.3A4.7 4.7 0 0 1 12 6.9a4.7 4.7 0 0 1 8.5 2.8C20.5 15.9 12 21 12 21Z'
FILES = ('sponsor.css', 'sponsor.js', 'sponsor-face.webp', 'sponsor-portrait.webp')


def _hashed(name):
    path = SITE/name
    stem, _, ext = name.rpartition('.')
    return f'{stem}-{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}.{ext}'


ASSETS = {name: 'assets/'+_hashed(name) for name in FILES}

PILL = (f'<button type="button" class="sp-pill" aria-haspopup="dialog" aria-controls="sponsor-dialog" aria-label="Sponsor">'
        f'<span class="sp-face" aria-hidden="true"><img src="{ASSETS["sponsor-face.webp"]}" alt="" width="26" height="26">'
        f'<svg viewBox="0 0 24 24"><path d="{HEART}"/></svg></span><span class="sp-label">Sponsor</span></button>')

DIALOG = (
    '<dialog id="sponsor-dialog" class="sp-dialog" aria-labelledby="sponsor-title">'
    '<div class="sp-head"><h2 id="sponsor-title">Sponsor</h2>'
    '<button type="button" class="sp-close" aria-label="Close"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div>'
    '<div class="sp-sheet">'
    f'<div class="sp-hero" aria-hidden="true"><span class="sp-portrait"><img src="{ASSETS["sponsor-portrait.webp"]}" alt="" width="112" height="112" loading="lazy">'
    f'<svg viewBox="0 0 24 24"><path d="{HEART}"/><ellipse cx="7.6" cy="9.6" rx="1.5" ry="2.1" transform="rotate(-30 7.6 9.6)"/></svg></span>'
    '<span class="sp-spark sp-s1">✦</span><span class="sp-spark sp-s2">✦</span><span class="sp-spark sp-s3">✦</span></div>'
    "<p class=\"sp-lead\">I make GenZui out of love for characters, and I've put several hundred dollars of my own into it. "
    "I don't have a job, and my small TA pay doesn't cover rent and food. Some days I can barely afford to eat.</p>"
    '<p class="sp-ask">Please help me keep going 🥺 Even one dollar helps me eat today.</p>'
    '<div class="sp-how"><h3>How to help</h3><ol class="sp-steps" role="list"><li>Tap Ko-fi below.</li><li>Pick any amount. Small is fine.</li>'
    '<li>Pay with PayPal or a card. No sign-up needed.</li></ol></div>'
    '<a class="sp-kofi" href="https://ko-fi.com/mkpoli" target="_blank" rel="noreferrer noopener"><span class="sp-mark" aria-hidden="true">'
    '<svg viewBox="0 0 24 24"><path d="M4 9h12v6a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4ZM16 11h2a2.5 2.5 0 0 1 0 5h-2M7 3v3M11 2v3M15 3v3"/></svg></span>'
    '<span class="sp-copy"><strong>Ko-fi</strong><small>One-time or monthly</small></span>'
    '<svg class="sp-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 6l6 6-6 6"/></svg></a>'
    '<a class="sp-company" href="mailto:mkpoli@mkpo.li?subject=Sponsorship%20on%20genzui.mkpo.li">'
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v12H3zM3 7l9 6 9-6"/></svg>'
    "<span class=\"sp-copy\"><strong>Company sponsorship</strong><small>I'd love to put your ad on this site. Please write to mkpoli@mkpo.li.</small></span></a>"
    '<p class="sp-thanks">Thank you for reading this far. Your help keeps me fed and keeps GenZui growing 💗</p>'
    '</div></dialog>')


def write_assets(directory):
    """Copy the pill's stylesheet, script and portraits under their hashed names."""
    for name in FILES:
        (directory/ASSETS[name].removeprefix('assets/')).write_bytes((SITE/name).read_bytes())


def inject(page):
    """Place the pill first in the page's action group and the dialog before the script."""
    # Family pages: before the weight control, which hides on narrow desktops.
    page, n = re.subn(r'(<div class="weight-control header-weight")', lambda m: PILL+m[1], page, count=1)
    if not n:  # comparison page
        page, n = re.subn(r'(<a class="header-download")', lambda m: PILL+m[1], page, count=1)
    if not n:  # landing: the weight switch in the prompt row
        page, n = re.subn(r'(<button class="wt hud")', lambda m: PILL+m[1], page, count=1)
    if not n:  # gallery and Minnan pages: a plain header ending in a nav or a version label
        page, n = re.subn(r'(<span>[^<]*</span>|<nav aria-label="Main navigation">.*?</nav>)</header>',
                          lambda m: f'<div class="sp-end">{PILL}{m[1]}</div></header>', page, count=1, flags=re.S)
    assert n, 'No header to place the Sponsor pill in.'
    link = f'<link rel="stylesheet" href="{ASSETS["sponsor.css"]}">'
    script = f'<script src="{ASSETS["sponsor.js"]}" defer></script>'
    head = page.index('</head>')
    page = page[:head]+link+page[head:]
    end = page.rindex('</body>')
    return page[:end]+DIALOG+script+page[end:]
