# GenZui Serif 0.114

GenZui Serif / 源萃明朝 is a Japanese Mincho derived from
Noto Serif JP, Noto Serif Hentaigana, Noto Serif CJK JP and FRB Taiwanese Kana.

The font contains 17,090 encoded characters, including 286 hentaigana, seven
Unicode 18 kana additions, historical kana ligatures, and 13 Minnan tone
letters. Twenty-one historical kana forms are GenZui constructions. Archaic WU has a curved
default and a hooked alternate selected by `ss01`.

Version 0.114 adds an Okinawan home-page composer, with Funatsu’s 27 forms and
eight raised katakana. The font uses 26 documented PUA positions; voiced forms
and YI/YE use combining dakuten where possible. The specimen also retains
separate collections for Han numerals, tally marks and description characters.
All 763 characters identified by Unicode 18’s Hiragana/Katakana Script and
Script_Extensions properties are covered.
Unencoded historical variants and arbitrary combining sequences remain outside
this encoding audit.

Regular is the available weight. Shared ideographs use Japanese regional forms.
The font is distributed under SIL OFL 1.1; source notices accompany the download.

The specimen site is https://genzui.mkpo.li/. Related typeface:
[Kureedo](https://kureedo.mkpo.li/), based on Klee One.

## Site build

`bun install --frozen-lockfile`, then `bun run release:build`. The build requires
the checked font package in `dist/` and its matching checks in `build/serif/`.
`bun run deploy:check` validates the Cloudflare configuration. The production
branch is `main`; deploy with `bun run deploy` after committing the release.

`releases/v0.114/` contains the immutable font assets. Preserve all versioned
directories when building subsequent releases. The site exposes both pinned
CSS (`/v0.114/genzui.css`) and a current alias (`/genzui.css`).

The release image uses the distributed font's glyphs. Its text alternative is:
“源萃明朝 / GenZui Serif. Six historical kana: KOTO, TOKI, TOMO, TOTE,
alternate NE and alternate WI. 17,090 characters; 286 hentaigana; Unicode 18.0. Based on Noto Serif JP,
Noto Serif Hentaigana and FRB Taiwanese Kana. genzui.mkpo.li.”
