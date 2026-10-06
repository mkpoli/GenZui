# GenZui Sans Han

GenZui Sans Han / 源萃ゴシック漢字 is a separate download beside GenZui Sans.
Together the two cover all 103,383 characters that Unicode 18 assigns in the
CJK Unified Ideographs blocks (URO and Extensions A–J), the two Compatibility
Ideographs blocks, Kangxi Radicals, CJK Radicals Supplement, CJK Strokes and
Ideographic Description Characters. GenZui Sans Regular covers 14,129 of
them; GenZui Sans Han holds the other 89,254.

## Sources

Each code point takes the first source in this order that maps it:

| Order | Source | Characters | Forms |
| --- | --- | --- | --- |
| 1 | [Noto Sans CJK JP](https://github.com/notofonts/noto-cjk) Regular | 16,546 | Source Han Sans, Japanese |
| 2 | [Sukima Gothic](https://booth.pm/ja/items/2117070) 11.41 Main | 34,395 | Japanese; Source Han Sans 1.002 base via Genshin Gothic |
| 3 | Sukima Gothic 11.41 Sub | 2,610 | as above |
| 4 | [Plangothic](https://github.com/Fitzgerald-Porthmouth-Koenigsegg/Plangothic_Project) P1 2.9.5795 | 25,168 | Source Han Sans CN, Chinese Mainland |
| 5 | Plangothic P2 2.9.5795 | 10,535 | as above |

Noto Sans CJK JP comes first because GenZui Sans is built on its design.
Sukima Gothic follows because its author drew Japanese forms for the
ideographs of 文字情報基盤, 戸籍統一文字 and 行政事務情報文字. Its readme
notes that a few characters sit at the code point its author judged correct
where IPAmj Mincho uses another. Plangothic fills the rest, mostly extension
ideographs, with Chinese Mainland forms; its README states that some differ
from the Unicode code charts. `build/sans-han/sources.json` records the
source of every character.

Sukima Gothic and Plangothic have one weight, Regular, so the supplement has
no Bold.

## Conversion

Noto Sans CJK JP's CFF curves are converted to quadratic curves (maximum
error 0.3 units). Sukima Gothic's 1024-unit outlines are scaled to the
1000-unit em; Plangothic is copied unchanged. Hinting is dropped. Ten Sukima
Gothic ideographs carry stray widths between 984 and 1010 units; they get the
1000-unit width with the ink kept centred, and `sources.json` lists them. Vertical
metrics use a 1000-unit advance with the origin at 880, the Source Han Sans
em box. Line metrics copy GenZui Sans, so mixed lines keep their height.

## File split

A font holds at most 65,535 glyphs. The supplement is split by plane, so
each new Unicode extension lands in a predictable file:

| File | Planes | Characters |
| --- | --- | --- |
| GenZuiSansHan-Regular | BMP and plane 3 (URO, Extension A, compatibility, radicals, strokes, Extensions G, H and J) | 28,172 |
| GenZuiSansHanSIP-Regular | plane 2 (Extensions B–F, I and the compatibility supplement) | 61,082 |

`genzui-sans-han.css` gives both files the CSS family `GenZui Sans Han` with
exact `unicode-range` lists, so a browser fetches a file only for a page that
uses one of its characters. Installed, the files appear as GenZui Sans Han and
GenZui Sans Han SIP.

## Checks

`scripts/check_sans_han.py` requires that GenZui Sans and the two files cover
the whole repertoire with no character in two files, that each file stays in
its planes and under the glyph limit, that every outline's bounds stay within
two units of its source, and that HarfBuzz shapes a sample of each file in
both directions without `.notdef` and with 1000-unit vertical advances.

## Licences

Noto Sans CJK, Sukima Gothic and Plangothic are licensed under SIL OFL 1.1.
Plangothic reserves the names "Plangothic" and "遍黑"; Adobe reserves
"Source". Sukima Gothic includes M+ OUTLINE FONTS glyphs under the M+ FONTS
LICENSE. The package carries each licence, Sukima Gothic's readme and the
pinned source manifest. Sukima Gothic needs a signed-in BOOTH download, so
`sources/han-manifest.json` pins its checksum and the build stops with
instructions when the archive is absent.
