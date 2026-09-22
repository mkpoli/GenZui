GenZui Serif / 源萃明朝（げんずい）
Regular, version {{VERSION}}

One font for Japanese text and historical kana:
  17,090 encoded characters from the Noto Serif JP base and kana additions
  27 Funatsu Okinawan forms and eight raised katakana
  26 PUA bases; other forms use standard combining dakuten
  See okinawan-mappings.json and the home-page Okinawan input tool.
  13 Minnan tone letters with overline and dot-below support
  286 hentaigana
  All seven Unicode 18 kana additions
  Four CJK-encoded kana ligatures: U+2A708, U+2CEFF, U+2CF00, U+2CF02
  All 763 characters in Unicode 18's Hiragana/Katakana Script and Script_Extensions
  卄, five ideographic tally marks and all 17 ideographic-description characters
  340 historical characters and transcription symbols in the inventory

INSTALL ON WINDOWS

Double-click GenZuiSerif-Regular.ttf and choose Install. The family appears as
GenZui Serif or 源萃明朝 depending on the application's language. Reopen an
application if its font list does not update.

The optional Install-GenZui.ps1 installs for the current Windows user, verifies
the font against checks.json, and checks the registered Regular face. To run
it from PowerShell in this folder:

  powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-GenZui.ps1

Installing the font makes it available to applications. Browser fallback still
depends on the page and browser settings. For a page you control:

  font-family: "GenZui Serif", "源萃明朝", serif;

READ AND REVIEW

Open serif-proof.html for an offline specimen with the embedded font. It includes
editable mixed text, vertical text, combining marks, all hentaigana, and a table
of the added forms. The WOFF2 file is provided for web embedding.

Twenty-one historical forms use Noto components and original drawing.
SQUARE PAATU (U+332C) uses Noto's small squared-katakana components in both
writing directions. kana-coverage.json records encoded character coverage;
unencoded historical variants and arbitrary combining sequences are outside its scope.
Historical katakana use Mincho kana strokes. Hiragana NARI is a new drawing
with an opening diagonal, a rounded low shoulder and a lighter rising exit,
aligned to the kana baseline.
Regular is the available weight;
bold text may be synthesized by the application. Shared ideographs use Japanese
regional forms. Chinese and Korean coverage follows the Noto Serif JP base, with 卄 added from Noto Serif CJK JP.

Minnan tone letters come from FRB Taiwanese Kana. Vertical tone placement
supports one to four fullwidth kana at default advance and zero letter spacing.
Use separate ruby runs for each syllable. Longer groups or custom spacing
require application-level positioning.

WU VARIANTS

U+1B11F uses a curved descent by default. Enable stylistic set 1, named
"Hooked WU", to use the broad outward bow and compact drawn return. Both stems start inside
the upper bar. Applications need OpenType stylistic-set controls to select it.
For web text: font-feature-settings: "ss01" 1;

SOURCES AND LICENCES

Noto Serif JP and Noto Serif Hentaigana supply the base and historical outlines
under SIL OFL 1.1. FRB Taiwanese Kana supplies 13 tone letters and two marks
under OFL 1.1; its original licence and README are included. Noto Serif CJK JP supplies 卄; its original OFL is included as NotoSerifCJK-OFL.txt.
The combined font
is distributed under SIL OFL 1.1. Jigmo2 supplied the NARI outline in comparison
fonts through 0.102 under CC0; its licence and notices accompany the comparisons.
See OFL.txt and NOTICE.txt.

source-manifest.json pins upstream files and checksums. sources.json describes
each addition. checks.json records font validation; browser-checks.json records
browser verification. Unicode data terms are in Unicode-LICENSE.txt. The installer
uses the MIT licence in LICENSE-scripts.txt.
