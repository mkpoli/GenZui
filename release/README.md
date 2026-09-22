# GenZui Serif 0.114

GenZui Serif / 源萃明朝 is a Japanese Mincho derived from
Noto Serif JP, Noto Serif Hentaigana, Noto Serif CJK JP and FRB Taiwanese Kana.

The font contains 17,090 encoded characters, including 286 hentaigana, seven
Unicode 18 kana additions, historical kana ligatures, and 13 Minnan tone
letters. Twenty-one historical kana forms are GenZui constructions. Archaic WU has a curved
default and a hooked alternate selected by `ss01`.

Version 0.114 adds an Okinawan composer to the Serif page, with Funatsu’s 27 forms and
eight raised katakana. The font uses 26 documented PUA positions; voiced forms
and YI/YE use combining dakuten where possible. The specimen also retains
separate collections for Han numerals, tally marks and description characters.
All 763 characters identified by Unicode 18’s Hiragana/Katakana Script and
Script_Extensions properties are covered.
Unencoded historical variants and arbitrary combining sequences remain outside
this encoding audit.

Regular is the available weight. Shared ideographs use Japanese regional forms.
The font is distributed under SIL OFL 1.1; source notices accompany the download.

The site is https://genzui.mkpo.li/: a landing page with both families, the Serif page at /serif and the Sans page at /sans. Related typeface:
[Kureedo](https://kureedo.mkpo.li/), based on Klee One.

## GenZui Sans 0.101

GenZui Sans / 源萃ゴシック is the gothic family, derived from Noto Sans JP,
Noto Sans Hentaigana, GenSeki Hentaigana Gothic, Noto Sans CJK JP and FRB
Taiwanese Kana. It contains 17,070 encoded characters with the Serif family's
historical repertoire. The hentaigana are compiled at weight axis 380, where
their stems match Noto Sans JP Regular's hiragana; KOTO, the alternate NE and the
small archaic YE are refitted to their kana neighbours.

The page is https://genzui.mkpo.li/sans. `releases/sans-v0.101/` holds the
immutable font assets; the site exposes `/sans-v0.101/genzui-sans.css` and the
current alias `/genzui-sans.css`. The release image's text alternative is:
“源萃ゴシック / GenZui Sans. Archaic WU, then GenZui drawings: refitted KOTO, alternate NE
and small archaic YE, SQUARE PAATU and a tally mark. 17,070 characters; 286 hentaigana; Unicode 18.0.
Based on Noto Sans JP, Noto Sans Hentaigana and GenSeki Hentaigana Gothic.
genzui.mkpo.li/sans.”

## Site build

`bun install --frozen-lockfile`, then `bun run release:build`. The build requires
the checked font packages in `dist/` and their matching checks in `build/serif/`
and `build/sans/`.
`bun run deploy:check` validates the Cloudflare configuration. The production
branch is `main`; deploy with `bun run deploy` after committing the release.

`releases/v0.114/` and `releases/sans-v0.101/` contain the immutable font assets.
Preserve all versioned directories when building subsequent releases. The site exposes both pinned
CSS (`/v0.114/genzui.css`) and a current alias (`/genzui.css`).

The home page's share image shows both families from the distributed fonts'
glyphs. Its text alternative is: “源萃 / GenZui: GenZui Serif 源萃明朝 and GenZui
Sans 源萃ゴシック. Archaic WU, KOTO and alternate NE in both families. 17,090 and 17,070
characters; 286 hentaigana; Unicode 18.0. Based on Noto Serif JP, Noto Sans JP
and Noto Hentaigana. genzui.mkpo.li.” The Sans page has its own card,
described under GenZui Sans below.
