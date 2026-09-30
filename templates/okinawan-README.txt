GenZui Serif Okinawan / 源萃明朝 沖縄文字
Regular and Bold, version {{VERSION}}

{{COUNT}} encoded characters: ordinary hiragana and katakana, Latin letters,
numbers, punctuation, 27 Funatsu New Okinawan Kana forms and eight raised
katakana used in shimakutuba notation. The same Okinawan outlines are included
in the full GenZui Serif family.

This subset supports kana sentence specimens. Kanji and historical kana beyond
this repertoire require the full GenZui Serif font or another fallback font.

INSTALL

Open GenZuiSerifOkinawan-Regular.ttf and GenZuiSerifOkinawan-Bold.ttf and install
both. Select GenZui Serif Okinawan in your application.

For web use, keep the WOFF2 files beside genzui-okinawan.css and load that CSS.
Set font-family: "GenZui Serif Okinawan", serif;

Open index.html for editable Regular and Bold specimens. Its fonts are local;
no network connection is required. Copy special characters from the specimen
or use the Okinawan composer at https://genzui.mkpo.li/serif#okinawan.

ENCODING

okinawan-mappings.json records all 35 forms. There are 26 PUA base characters;
voiced forms and YI/YE use combining dakuten where applicable. Keep each base
and its following U+3099 together. An application needs OpenType shaping to
compose the dakuten. The raised katakana use half-em advances for horizontal
text. Their private-use code points follow the documented Xim Sans convention.

LICENCE

SIL Open Font License 1.1. Copyright and licence metadata are retained from
the full GenZui Serif family. See OFL.txt, NOTICE.txt and the source licences.
sources.json identifies the parent fonts; checks.json verifies matching
outlines, metrics, shaping and TTF/WOFF2 content.
