# Kana type design

A pair of Noto-derived serif and sans fonts for historical Japanese kana.
The family name is undecided. Both families target the same historical repertoire,
including all 286 Unicode hentaigana and the seven kana introduced in Unicode 18.0.

The current material consists of a source coverage audit, sixteen experimental
sans forms, and a [survey of existing hentaigana fonts](research/existing-fonts.md).
Production fonts have not been built. Noto Sans Hentaigana source and the released
GenSeki Hentaigana Gothic provide further outline sources to evaluate.

## Sources

| Source | Role | Historical characters covered |
| --- | --- | ---: |
| Noto Serif JP | Modern text and serif construction reference | 2 |
| Noto Sans JP | Modern text and sans construction reference | 2 |
| Noto Serif Hentaigana | Hentaigana outlines and historical reference | 290 |

These counts use the 309-character repertoire in `research/repertoire.json`:
286 hentaigana, 11 other letters and digraphs in Kana Supplement and Kana
Extended-A, 10 small kana, and the two digraphs ゟ and ヿ. The latter two are the
characters already covered by the JP fonts. CJK-encoded kana ligatures such as
𪜈 U+2A708 are outside this initial inventory.

CODH's [hentaigana page](https://codh.rois.ac.jp/char-shape/hentaigana/) presents
both NINJAL's font and Noto Serif Hentaigana. The outline source here is
[Noto Serif Hentaigana](https://github.com/notofonts/hentaigana), released under
the SIL Open Font License. No NINJAL outlines or scanned specimen images are
embedded in the proofs.

## Unicode 18 additions

| Code point | Character |
| --- | --- |
| U+1B123 | Hiragana digraph KOTO |
| U+1B124 | Katakana digraph TOKI |
| U+1B125 | Katakana digraph TOTE |
| U+1B126 | Katakana digraph YORI |
| U+1B127 | Katakana letter ALTERNATE NE |
| U+1B128 | Katakana letter ALTERNATE WI |
| U+1B168 | Katakana letter SMALL ARCHAIC YE |

The last character is in Small Kana Extension. None of the three pinned source
fonts covers these seven characters. Character names, ages, decompositions and
vertical orientation come from the Unicode 18.0.0 data files; the host Python
Unicode database is not used for this inventory.

References: [Kana Extended-A chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B100.pdf),
[Small Kana Extension chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-1B130.pdf).

## Reproduce the audit and proofs

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/sources.py
.venv/bin/python scripts/repertoire.py
.venv/bin/python scripts/proof.py
.venv/bin/python scripts/check.py
```

`sources/manifest.json` pins each font to a Git commit and records every source
file's SHA-256. Downloads are verified before use. A cached source with an
unexpected checksum causes a build error.

`build/proof/index.html` is a self-contained comparison with embedded fonts,
size control and horizontal/vertical text. Its sixteen forms cover simple strokes,
loops, intersections and denser constructions. `build/proof/preview.png` shows
eight of them. The study construction is recorded in `build/proof/sources.json`
and [research/design.md](research/design.md).

## Windows browsers

[Browser setup](browser/README.md) describes Firefox fallback preferences and the
Chrome/Vivaldi userscript. Build its local setup page with
`python3 scripts/browser_setup.py`. The helper uses installed fonts and does not
create a new font family.

## Licence

Source fonts and derived outlines use SIL OFL 1.1. Each upstream notice is in
`sources/upstream/<family>/OFL.txt` and is embedded in the HTML proof. Unicode
data uses the notice in `sources/Unicode-LICENSE.txt`. Project scripts use the
MIT licence in `LICENSE-scripts.txt`.
