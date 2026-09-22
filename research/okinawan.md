# Okinawan kana in GenZui

GenZui supplies all 27 forms in Funatsu’s New Okinawan Kana chart and the eight
raised katakana used in Okinawa Prefecture’s notation guide. The home page has a
composer for each system, with kana input, explicit shortcuts and optional romaji
conversion. Text is processed locally. This is a browser composer, not an
operating-system IME.

## Storage

[data/okinawan/mappings.json](../data/okinawan/mappings.json) is the shared mapping
registry for the font, composer, character inventory and downloadable reference.
It identifies the sources and preferred output for every form. Its schema version
is independent of the font version.

Ordinary kana retain their Unicode values. YI is `U+3044 U+3099` (い゙), and YE is
`U+3048 U+3099` (え゙). The other seven voiced forms use a private-use base followed
by `U+3099 COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK`. A `ccmp` lookup renders
each as a composed glyph; the stored text remains the two-character sequence.
These preferences are application conventions, not Unicode decomposition rules.

There are 26 newly encoded PUA positions, taking the font total to 17,090:

| Funatsu base | PUA | Funatsu base | PUA |
| --- | --- | --- | --- |
| TU | F450 | TI | F452 |
| KWA | F454 | KWI | F456 |
| KWE | F458 | HWA | F45A |
| HWI | F45B | HWE | F45C |
| Glottal YA | F45D | Glottal YU | F45E |
| Glottal YO | F45F | Glottal WA | F460 |
| Glottal WI | F461 | Glottal WE | F462 |
| Glottal N | F463 | WU | F465 |
| SI | F467 | TSI | F469 |

These are the corresponding positions in Nishiki-teki’s PUA convention. The
composer accepts Nishiki-teki’s nine remaining values (F451, F453, F455, F457,
F459, F464, F466, F468, F46A) and converts them to the preferred sequences. Those
nine duplicate values are not encoded in the font.

| Raised katakana | PUA (Xim Sans convention) |
| --- | --- |
| ア | E532 |
| イ | E533 |
| ウ | E534 |
| エ | E535 |
| オ | E536 |
| ツ | E537 |
| フ | E4EF |
| ン | E5AA |

PUA assignments depend on agreement between the document and font. They do not
acquire standard character meanings through this implementation. The proposals’
provisional numbers are not used. U+1B168 remains SMALL ARCHAIC YE. The legacy
FKOkinawan FA80–FA9A encoding overlaps assigned CJK characters and is not
interpreted as Okinawan input. The composer normalizes kana voicing sequences
without changing CJK compatibility ideographs.

## Input

In **Kana & shortcuts**, a Japanese IME can supply ordinary text. Funatsu digraphs
such as とぅ, てぃ, くゎ and すぃ become the corresponding single-cell forms. Existing
kanji, Latin text and punctuation remain intact. Prefectural mode leaves ordinary
kana as entered. Use a Japanese katakana IME or select romaji input for katakana.

Every palette key inserts a brace shortcut, such as `{tu}` or `{'ya}`, into the
source selection. Shortcuts work in both input modes. Glottal-initial YA, YU, YO,
WA, WI, WE and N are explicit choices; the composer does not guess them from
word position. Funatsu’s chart restricts these forms to word beginnings.

**Romaji & shortcuts** converts lowercase input using a documented keyboard
convention. `tu ti si tsi` select the corresponding Funatsu forms; `tsu chi shi`
produce つ, ち, し. `du di gwa gwi gwe zi dzi` produce the voiced sequences.
`hwa hwi hwe` select the labial forms. `yi ye` use Unicode combining sequences.
In prefectural mode, `ti tu si tsi` produce ティ, トゥ, スィ, ツィ. Other standard
kana, palatalized syllables and explicit small-kana inputs (`xa`, `xtsu`, etc.)
are available. `n'` separates a nasal from a following vowel, doubled consonants
produce small っ/ッ, and `-` produces ー. Uppercase text and punctuation pass through.
Unrecognized romaji or brace shortcuts remain visible and produce a warning.

Raised katakana use `^a ^i ^u ^e ^o ^tsu ^fu ^n`, or their brace shortcuts.
For example, `^uウトゥ` contains raised ウ followed by ウトゥ. In the prefectural
guide this distinguishes “husband” from ウトゥ “sound”. The eight signs serve
different functions across the guide’s language varieties; the composer does not
translate between systems or infer pronunciation. Romaji keys are input commands,
not a proposed linguistic romanization.

The editor respects Japanese IME composition, keeps separate drafts for the two
systems, and exposes the resulting code points. Copy supplies plain text; the
receiving application needs GenZui or a font with matching PUA mappings.

## Drawings

The 27 Funatsu forms use original contours drawn as complete strokes in
[`scripts/okinawan_drawings.py`](../scripts/okinawan_drawings.py). Funatsu’s chart
and FK Okinawa Mincho establish the distinguishing strokes. FROkinawanMoji,
MgenKana+ and Nishiki-teki provide further comparisons of letter proportions.
No outlines from those fonts or Xim Sans are included in GenZui.

TU and WU have a broad lower return. TI, KWI and TSI continue into a full lower
stroke. The labial forms share a continuous ふ body, widened to keep the weight
of a full ふ; the following vowel is drawn at its own size, HWI’s close to full
height as in the chart. Glottal YA carries its diagonal above the arc, glottal
YU and YO a full-height stroke on the left, and glottal WA, WI and WE a level
bar above the letter, all following the chart. Voiced forms have consistent
dakuten placement. YI and YE also have dedicated drawings, reached through
their existing Unicode sequences. Noto’s original outlines and layout tables
remain intact; two appended composition lookups select the Okinawan forms.

When the font is assembled, each joined letter is fitted to the Noto kana it
extends (`BASES`): the same vertical extent and baseline, centred in the em,
uniformly scaled, and never wider than 920 units. Every stroke is then
thickened by a small radius (`WEIGHT` sets exceptions) so the hairlines match
Noto’s kana weight in running text.

The eight raised katakana are not drawn separately. The prefectural guide sets
them as the text face’s own katakana at about half size, top-aligned with the
line (PDF page 5), so GenZui reduces Noto’s small kana ァィゥェォッㇷ, which
already carry the optical correction for a small size, thickens them slightly,
and places them at the top of a half-em cell; ン, which has no small kana, is
reduced from the full letter with more thickening (`RAISED`). Their design
target is horizontal text; the cited material does not establish a
vertical-layout convention for these signs. No other released font with these
signs was found apart from Xim Sans.

After building the checked font and specimen site,
`scripts/okinawan_proof.py --references <reference-directory>` builds a local
comparison page in `build/okinawan`. It accepts `FK-Okinawa-reference.ttf`,
`nishiki-teki.ttf`, `mgenkanaplus.woff2`, `Xim-Sans-Handwritten.ttf`, Funatsu’s
chart `funatsu-chart.pdf` (its embedded letter font is extracted with `mutool`
and shown as “Funatsu’s chart”) and the published FROkinawanMoji specimen
`frokinawa-sample.jpg`. Each card also shows the ordinary kana the letter
joins or modifies, set in GenZui. Reference files stay
in the ignored study output and are excluded from the release build. The font
size control and reference selector apply to all 35 forms.

## References

- [Funatsu’s 2016 complete chart](https://raw.githubusercontent.com/ctrlcctrlv/OkinawanKanaUnicodePaper/main/mojiichiran.pdf): all 27 forms, contrasts, examples and word-initial restrictions. The PDF embeds Funatsu’s own letter font (an EUDC TrueType subset), the primary shape reference for the redraw.
- [Brennan’s 2023 proposal](https://raw.githubusercontent.com/ctrlcctrlv/OkinawanKanaUnicodePaper/main/okana.pdf): 18 bases, seven voiced derivatives and two existing Unicode sequences.
- [Okinawa Prefecture’s guide](https://www.pref.okinawa.lg.jp/_res/projects/default_project/_page_/001/009/625/02_shimakutubahyouki.pdf): PDF page 5 sets the raised signs in running text (half-size, top-aligned katakana of the text face); pages 11–12 (printed 8–9) and 26 (printed 22) illustrate them further.
- [L2/23-118](https://www.unicode.org/L2/L2023/23118-ryukyu-kana.pdf): the eight-sign proposal and samples. Proposed positions are not assignments.
- [Nishiki-teki PUA chart](https://umihotaru.work/nishiki-teki_pua.pdf): the Funatsu F450–F46A convention.
- [Xim Sans 1.62](https://github.com/XimcoYuzuriha/Xim_Sans/tree/main/ver_01_62): the eight raised-sign PUA mappings in the author’s unencoded-character documentation.
- [Toranekoman’s kana fonts](https://newjapanese.blog.jp/archives/14540652.html): an existing partial implementation. The inspected Mkana+, MgenKana+ and Ricty Kana webfonts cover six positions in the Funatsu range (F450–F453, F469–F46A).
- Toranekoman’s [substitute converter](https://toracatman.github.io/ConvertSubstitute/) and [Latin/kana converter](https://toracatman.github.io/ConvertLatinHiraganaKatakana/): precedents for browser input tools.
- [FROkinawaMoji](https://booth.pm/ja/items/1003982): another Funatsu font reference.
- [しま書体](https://shimanomoji.site/how.html): a separate orthography and Latin-input font workflow. Its input conventions are not interchangeable with either system implemented here.

## Verification

Run `node scripts/check_okinawan_input.cjs` for conversion and storage checks.
`python scripts/check_serif.py` includes the 35-form shaping audit, unknown-script
PUA runs, TTF/WOFF2 parity, raised metrics and neighboring Japanese kana.
The existing complete Noto outline, metrics and shaping regression checks remain
in force. Browser checks exercise input composition, selection replacement,
system drafts, copying fallback, responsive layout and the PUA inventory.
