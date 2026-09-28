# Okinawan kana in GenZui Serif

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

The two Okinawan systems use 26 PUA positions:

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

The new outlines use Noto Serif JP components and GenZui drawing. No outlines from
Nishiki-teki, Xim Sans, Toranekoman’s fonts or FROkinawaMoji are redistributed.
The Funatsu chart and proposal establish the shapes and distinguishing strokes.
The constructed forms remain provisional, as do GenZui’s other drawn additions.
Raised katakana have a half-em advance and sit in the upper half of the line.
Their design target is horizontal text; the cited material does not establish a
vertical-layout convention for these eight signs.

The glottal letters and SI keep Noto’s kana whole and add one Noto stroke. In
glottal YA the top of は’s left stroke joins the head of や’s arm as one outline;
two new curves meet each edge with its own direction and curvature. The others
set the stroke apart: は’s left stroke beside ゆ and above よ’s loop, い’s falling
stroke beside ん, ぃ’s second stroke beside す, and こ’s upper stroke over ゐ, ゑ
and the WA body, which is ゐ with わ’s loop in place of its inner loop. A kana
narrowed to make room gets the lost width back sideways. Positions, sizes and
stroke widths were chosen by comparing variants side by side; the choices are
kept in [research/okinawan-arena](okinawan-arena). Bold takes the same strokes
from Noto Serif JP at weight 700.

## References

- [Funatsu’s 2016 complete chart](https://raw.githubusercontent.com/ctrlcctrlv/OkinawanKanaUnicodePaper/main/mojiichiran.pdf): all 27 forms, contrasts, examples and word-initial restrictions.
- [Brennan’s 2023 proposal](https://raw.githubusercontent.com/ctrlcctrlv/OkinawanKanaUnicodePaper/main/okana.pdf): 18 bases, seven voiced derivatives and two existing Unicode sequences.
- [Okinawa Prefecture’s guide](https://www.pref.okinawa.lg.jp/_res/projects/default_project/_page_/001/009/625/02_shimakutubahyouki.pdf): PDF pages 11–12 (printed 8–9) and 26 (printed 22) illustrate the raised signs.
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

### Ligature outlines and Bold proof

The approved placement outlines are stored in
`data/okinawan/ligatures.json`, in a 1000-unit font coordinate system.
`scripts/okinawan_bold.py` composes both weights from native Noto Serif JP
masters. TI, KWI and SI retain their confirmed bodies in both weights;
HWI, KWE and HWA also retain their accepted B outlines in both weights.
TSI/DZI retain Regular A and Bold B. KWA
joins the diagonal and bowl into one continuous outline, removing the
component caps, and centers its bounds in the 1000-unit advance. Its weights
follow Regular A and Bold B. HWA uses the accepted B native つ shoulder
turn. Bold HWA reduces
the bowl counter to restore weight after the narrow fit.

The fuller proof uses these optical source weights:

| Component | Regular | Bold |
| --- | --- | --- |
| KWI body and vowel | 600 / 650 | 850 / 900 |
| KWE body and vowel | 550 / 500 | 850 / 900 |
| KWA body and complete わ | 500 / 700 | 700 / 900 |
| HWA connector and わ | 600 / 850 | 850 / 900 |
| TSI body and vowel | 650 / 600 | 900 / 900 |
| TU / WU entry and bowl | 600 / 650 | 850 / 900 |
| HWE diagonal and terminal | 650 / 650 | 850 / 850 |

Regular KWE combines the A く source with B え, using native 550/600
terminal donors for the two foot-weight choices while holding the baseline.
HWI Bold retains the earlier upright return, with a finite 18–20-unit cap
and a smooth taper confined to the top of the hook. Its axis aims toward
the beginning of the right い stroke.
HWE uses the same native rounded shoulder as HWA. Its upper え diagonal
stands more upright, while the lower native arch and terminal keep their
shape. The shoulder rises to match the HWA/HWI group.
HWA/HWI/HWE vowels share an optical baseline.

Native contours supply the terminals and bowls. TU keeps the rising つ
curve with its height reduced to 76%, giving the と entry more room. Its
balance follows R5-B. WU uses a broader bowl at 80% height and a longer
visible central を stem, following the R6 proportions. Both use heavier
native bowl donors to retain contrast after the vertical reduction. The
TU connection edges have separate tangent handles. WU uses native rounded
turns between its source entry and bowl, and retains its native
arch and rounded terminal, shortening only the straight stem sections.
No contour expansion is applied. The く, と and を entries match their
source kana’s top height;
TSI’s stronger つ reaches 25 units above its source top, with the dakuten
raised by the same amount. HWA’s reduced わ is stronger and vertically
fuller; its Bold placement leaves the small stroke separate from ふ.

Dakuten come from native ど, で, ぐ, ず and づ. Each pair retains its
outlines and internal spacing, with placement specific to the constructed
base. DI uses the native で positions; DZI has additional clearance above つ.
All voiced forms preserve the size of their unvoiced base.

After building both Serif weights, run:

```sh
.venv/bin/python scripts/okinawan_release_proof.py
.venv/bin/python scripts/check_okinawan_release_proof.py
.venv/bin/python scripts/okinawan_sns.py
show build/okinawan-release --name genzui-okinawan
```

Open the local URL printed by `show`. Each option displays the source kana,
constructed letter and vowel at the same size, with baseline and top guides.
Voiced forms appear in the same card. A shared HWA/HWI/HWE row compares
their vowel baselines. Regular and Bold choices are independent; confirmed
shapes are retained, with TI, KWE, HWI and HWA fixed to B. TSI uses
Regular A and Bold B. KWA uses Regular A and Bold B; its revised drawings remain open for review. Confirmed weights
start collapsed on every page load and remain available through native
disclosure controls. Open panels stay open across filtering and selection;
only unconfirmed history panels restore their open state after reload.
HWE, TU, WU and KWA appear first, and HWE includes the shared baseline
comparison. A jump to a fully confirmed character opens its panel. Copy choices for one character
or the complete set as JSON.

TU/WU also show the saved v1 and R1–R7 drawings, plus eight successive native
composition rounds. TSI/DZI include v1, R1–R3 and the native rounds, including
the accepted R3-B with only the right い part lowered 16 units.
`data/okinawan/design-history.json` stores 132 distinct outlines; identical
shapes share their round labels. Historical native voiced samples use the
current dakuten placement, as noted on their cards. Each appears beside
native kana at the same size. A selected historical reference is included
in the copied choice without changing the candidate font.

The `sns/` page contains Japanese and English announcement copy and two
2400px square sentence specimens rendered from the full candidate fonts.
Traditional proverbs follow the [University of Hawaiʻi handbook, lesson 3](https://manoa.hawaii.edu/okinawa/handbook_l3_proverbs.pdf),
pages 3-2 and 3-3. Line breaks and punctuation are editorial; the kana
digraphs are typeset as GenZui ligatures. Font hashes, source text and image
metadata are recorded in `specimens.json` beside the images.
