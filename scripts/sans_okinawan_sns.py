"""Render the two Sans Okinawan announcement cards from the staged release."""
from okinawan_sns import build as funatsu
from okinawan_raised_sns import build as raised
from sans_okinawan_release import FULL,SUB,VERSION
from sources import ROOT

if __name__=='__main__':
    out=ROOT/'build/sans-okinawan-social'
    funatsu(family='Sans',version=VERSION,font_out=FULL,output=out)
    raised(family='Sans',version=VERSION,font_out=SUB,full=FULL,output=out/'raised')

    from pathlib import Path
    page=out/'index.html'
    page.write_text(page.read_text().replace('<h2>日本語</h2>','<p><a href="raised/">上付きカタカナの投稿</a></p><h2>日本語</h2>'))
