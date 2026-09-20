# Kana type design

A Noto-derived serif extension for historical Japanese kana, developed separately
from Kureedo. The family name is undecided. GenSeki Hentaigana Gothic already
supplies the complete sans repertoire, so the current work concentrates on the
17 characters missing from Noto Serif JP and Noto Serif Hentaigana together.

The first Regular outline proof covers all 309 target characters. It retains
Noto Serif Hentaigana's 290 historical outlines, adds 17 provisional forms, and
imports the two existing JP digraphs. The internal family identifier is
`HK Serif Proof`; the outlines need typographic review before release.
The [font survey](research/existing-fonts.md) and the earlier sans study remain
available as research.

## Build the serif proof

After installing the dependencies and fetching the pinned sources below:

```sh
.venv/bin/python scripts/serif.py
.venv/bin/python scripts/check_serif.py
```

`build/serif/serif-proof.html` embeds the fonts and shows every addition beside
Noto Serif JP, with horizontal, vertical and combining-mark samples. The same
folder contains the installable `HKSerifProof-Regular.ttf`, WOFF2, outline
provenance and validation results. Only Regular is built. New shapes use Noto
components, including a newly drawn upper curve for hiragana KOTO.

Checks cover all 309 encoded forms, preservation of the 290 original historical
outlines and advances, ten vertical small-kana forms, 1,236 mark-shaping cases,
and matching TTF/WOFF2 output. These checks establish font behaviour; they do
not establish finished type design.

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
