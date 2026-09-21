# Existing hentaigana fonts

Sources checked on 20 September 2026. Availability and recent development are
recorded separately: an accessible download does not establish active maintenance.

| Font | Coverage and construction | Availability |
| --- | --- | --- |
| [源石変体仮名ゴシック / GenSeki Hentaigana Gothic](https://github.com/MihailJP/GenSekiHentaiganaGothic) | All 286 hentaigana and all seven Unicode 18 kana additions verified in the Regular font. Based on GenSeki Gothic, with forms from Shokaki, Sukima and its own additions. OFL 1.1. | Version 1.201, released 20 March 2026; Regular and Bold. |
| [すきまゴシック / Sukima Gothic](https://booth.pm/ja/items/2117070) | All 286 hentaigana verified in a public web subset. Based on Genshin Gothic, which derives from Source Han Sans and M+. Publisher identifies OFL 1.1. | Version 11.3, dated 19 April 2026. The author says large updates are now paused. |
| [しょかき変体仮名ゴチック / Shokaki Hentaigana Gothic](https://booth.pm/ja/items/5633978) | Partial repertoire, constructed from Source Han Sans JP Regular components. OFL 1.1. Some historical katakana occupy ordinary katakana positions. | Work in progress; latest listed update 7 September 2025. |
| [よくみる？変体仮名ゴシック](https://booth.pm/ja/items/555270) | Replaces selected ordinary hiragana with hentaigana forms in Genshin Gothic Normal. This does not provide full Unicode hentaigana coverage. OFL 1.1. | Download available in four weights. The author warns that Light, Regular and Medium use mechanically adjusted kana outlines. |
| [Noto Sans Hentaigana](https://github.com/notofonts/hentaigana/tree/main/sources/NotoSansHentaigana.glyphspackage) | Editable Glyphs package with Thin, Regular and Black masters. A direct Regular-master build encodes 285 of 286 hentaigana. U+1B001 has a drawing without a Unicode assignment. OFL 1.1. | Source at commit `3aa4d30ee04254d3d0a69c500de7fda494e3b302`, dated 5 June 2025. Repository archived 8 August 2026. Published release and HEAD build pages list Serif only. |
| [Koin変体仮名外字ゴシック（フリー版）](https://www.vector.co.jp/soft/winnt/writing/se489401.html) | 83 basic forms, 134 including voiced forms. Legacy Windows external-character font. Freeware; no open-outline licence established here. | Distribution page remains available. |
| [字躰帳変体仮名](https://booth.pm/ja/items/4889029) | Source Han Serif derivative, with a partial Unicode repertoire and additional forms in the private-use area. OFL 1.1. | First edition downloadable; publisher states that a second edition is in development in 2026. |
| [澄月 / てやんでぇ](https://www.morisawa.co.jp/culture/dictionary/13014) | Morisawa commercial families, each with all 286 Unicode hentaigana. | Listed by Morisawa; useful references for forms and naming. |

NINJAL's font remains available from its [official download page](https://cid.ninjal.ac.jp/kana/font/).
It is an IPAmj Mincho subset containing the 286 hentaigana, licensed under Apache
2.0. Its listed version is 1.01, dated December 2018.

## Serif gap source

[Jigmo](https://kamichikoichi.github.io/jigmo/), released 12 September 2025,
provides three Mincho fonts under CC0 1.0. The Jigmo2 binary was inspected for
U+2A708, U+2CEFF, U+2CF00 and U+2CF02: all four have nonempty outlines and
1024-unit horizontal and vertical advances. GenZui 0.100 imported these four
characters. Version 0.101 retains the baseline-adjusted hiragana NARI and redraws
the other three with Mincho kana strokes. The pinned archive and its CC0 dedication,
README and contributor notices are recorded in `sources/manifest.json`.

The separate Jigmo font covers archaic WU and nine historical small kana. The
GenZui constructions retain Noto components for consistency with the JP base.
Jigmo's 2025 release does not cover the seven Unicode 18 additions.

## Source verification

The GenSeki Regular binary from the official
[1.201 release](https://github.com/MihailJP/GenSekiHentaiganaGothic/releases/tag/v1.201)
was checked for cmap entries and nonempty outlines. All seven additions were
present at U+1B123–U+1B128 and U+1B168; the check did not rely on fallback or
private-use mappings. Its README also documents combining marks, vertical forms,
historical alternates and ligatures. These behaviours still need independent
shaping checks before adopting the font as a production source.

The Noto Sans source was compiled with fontmake 3.12.1 and glyphsLib 6.14.0:

```sh
fontmake -g sources/NotoSansHentaigana.glyphspackage -o ttf \
  --master-dir '{tmp}' --instance-dir '{tmp}' --output-dir build/sans-masters
```

This builds the three masters directly. It is a source inspection build, not an
official release. The current upstream `sources/config.yaml` builds only Serif.
Noto Sans has no encoded Unicode 18 additions. Its U+1B001 drawing is named
`archaicYe-hiragana` in the source and lacks a Unicode assignment.

The Sukima outline inspection used the public subset served by
[Zeoseven](https://fonts.zeoseven.com/items/895/), file
`a45c8428f6a76306.woff2`, SHA-256
`446ff08d7c728f87b9d70d6f8a2c297cf2f4efff8fcbe1e0aa251b1416694719`.
It contains all 286 hentaigana. This subset should not be assumed to match the
publisher's latest complete archive in every glyph or metadata field.

## Design observations

Shokaki's publisher specimen shows intentional stroke separation in U+1B060
(TA-4) and U+1B08B (NI-1). These forms support omitting some cursive connections
while preserving the character's structure. GenSeki's source table attributes
NI-1 to Shokaki and its own TA-4 to GenSeki Gothic components, so the two fonts
should not be treated as identical references.

For the next sans proof, compare the connected and separated forms individually.
Preserve distinctive loops and crossings, open cramped enclosed spaces, and set
terminal direction from the intended stroke. A constant-width stroke alone does
not resolve the topology or shape of a junction.

The direct comparison also shows different choices in U+1B006 (I-1): Noto
Sans retains the connected left curve, while the Shokaki-derived GenSeki form
separates the left strokes. In U+1B003 (A-2), GenSeki opens connections that Noto
Sans retains. These are character-specific design choices, not a rule to remove
all connections.
