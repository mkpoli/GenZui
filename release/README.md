# GenZui Serif 0.117

GenZui Serif / 源萃明朝 is a Japanese Mincho derived from
Noto Serif JP, Noto Serif Hentaigana, Noto Serif CJK JP and FRB Taiwanese Kana.

The font contains 17,090 encoded characters, including 286 hentaigana, seven
Unicode 18 kana additions, historical kana ligatures, and 13 Minnan tone
letters. Twenty-one historical kana forms are GenZui constructions. Archaic WU has a curved
default and a hooked alternate selected by `ss01`.

GenZui Serif has Regular and Bold, with the same characters. Bold's Noto
outlines come from the fonts' own Bold instances, and every stroke GenZui draws
has a Bold version of matching weight. TOMO, TOTE and TOKI share one position
for their TO stem, with their weight centred in the cell.

Version 0.117 raises TOMO's lower return, so the bars of its MO keep the spacing
of native モ and the ligature no longer reads tall. Bold YORI draws its strokes
at the weight of Noto Serif JP 650 and 95% size, so they match the kana beside
it while its three verticals stay apart.

The Serif page includes an Okinawan composer with Funatsu’s 27 forms and
eight raised katakana. The font uses 26 documented PUA positions; voiced forms
and YI/YE use combining dakuten where possible. The specimen also retains
separate collections for Han numerals, tally marks and description characters.
All 763 characters identified by Unicode 18’s Hiragana/Katakana Script and
Script_Extensions properties are covered.
Unencoded historical variants and arbitrary combining sequences remain outside
this encoding audit.

Regular and Bold are available. Shared ideographs use Japanese regional forms.
The font is distributed under SIL OFL 1.1; source notices accompany the download.

The site is https://genzui.mkpo.li/: a landing page with both families, the Serif page at /serif and the Sans page at /sans. Related typeface:
[Kureedo](https://kureedo.mkpo.li/), based on Klee One.

## GenZui Sans 0.103

GenZui Sans / 源萃ゴシック is the gothic family, derived from Noto Sans JP,
Noto Sans Hentaigana, GenSeki Hentaigana Gothic, Noto Sans CJK JP and FRB
Taiwanese Kana. It contains 17,070 encoded characters with the Serif family's
historical repertoire, in Regular and Bold. The hentaigana are compiled at
weight axis 380 (Regular) and 720 (Bold), where their stems match Noto Sans
JP's hiragana; KOTO, the alternate NE and the small archaic YE are refitted to
their kana neighbours. Bold takes every source at its Bold weight; the Minnan
tone letters and the drawn transcription symbols have Bold versions of
matching weight.

Version 0.103 replaces GenSeki's alternate WI 𛄨, which was narrower and lower
than the katakana around it, with a GenZui drawing from Noto Sans JP's own WI
and NA strokes in both weights.

The page is https://genzui.mkpo.li/sans. `releases/sans-v0.103/` holds the
immutable font assets; the site exposes `/sans-v0.103/genzui-sans.css`, which
declares both weights, and the current alias `/genzui-sans.css`. The release
image's text alternative is:
“源萃ゴシック / GenZui Sans, Regular and Bold. The name is set in Bold. Archaic WU
in Bold, then GenZui drawings: refitted KOTO, alternate NE and small archaic YE,
SQUARE PAATU and a tally mark, all in Bold. 17,070 characters; 286 hentaigana.
Based on Noto Sans JP, Noto Sans Hentaigana and GenSeki Hentaigana
Gothic. genzui.mkpo.li/sans.”

## Bold announcement

`scripts/bold_card.py` renders the card announcing Bold for both families to
`build/social/`, and `announcement-bold-ja.txt` / `announcement-bold-en.txt`
carry the post. The card's text alternative is:
“GenZui, Regular and Bold, on a dark green grid. 源萃明朝 GenZui Serif, on a light
card, shows archaic WU, KOTO, TOKI, TOTE, YORI, the alternate NE and WI, TOMO
and NARI in Regular above Bold. 源萃ゴシック GenZui Sans, on a dark card, shows the
refitted KOTO, alternate NE and small archaic YE, SQUARE PAATU, two tally marks,
and three ideographic description characters in Regular above Bold. Footer:
genzui.mkpo.li; 286 hentaigana, Unicode 18.0, free under SIL OFL 1.1.”

## Site build

`bun install --frozen-lockfile`, then `bun run release:build`. The build requires
the checked font packages in `dist/` and their matching checks in `build/serif/`
and `build/sans/`.
`bun run deploy:check` validates the Cloudflare configuration. The production
branch is `main`; deploy with `bun run deploy` after committing the release.

`releases/v0.117/` and `releases/sans-v0.103/` contain the immutable font assets;
each holds its family's Regular and Bold faces.
Preserve all versioned directories when building subsequent releases. The site exposes both pinned
CSS (`/v0.117/genzui.css`, with Regular at weight 400 and Bold at 700) and a current
alias (`/genzui.css`).

The home page's share image shows both families from the distributed fonts'
glyphs. Its text alternative is: “源萃 / GenZui: GenZui Serif 源萃明朝 and GenZui
Sans 源萃ゴシック. Archaic WU, KOTO and alternate NE in both families. 17,090 and 17,070
characters; 286 hentaigana; Unicode 18.0. Based on Noto Serif JP, Noto Sans JP
and Noto Hentaigana. genzui.mkpo.li.” The Sans page has its own card,
described under GenZui Sans below.

## Search metadata

Page titles, descriptions, Open Graph tags, Twitter cards and `WebSite` /
`WebPage` structured data are emitted by `scripts/release_site.py` and locked by
`scripts/check_release.py`. Canonical URLs, the Open Graph URLs and the home
page's structured data use `https://genzui.mkpo.li/`. `sitemap.xml` lists the
four HTML routes (`/`, `/sans`, `/gallery`, `/minnan`); section anchors, font
assets and release folders are not separate pages. `robots.txt` advertises the
sitemap, and `404.html` is `noindex`.

After deployment, check that `/robots.txt` includes the sitemap line,
`/sitemap.xml` returns XML with status 200, and a missing URL returns status
404. Submit `https://genzui.mkpo.li/sitemap.xml` in Google Search Console and
request indexing of the home and `/sans` pages through URL Inspection.
