# Unicode kana coverage in 0.112

GenZui covers all 763 characters identified by the Hiragana and Katakana values
of Unicode 18's Script and Script_Extensions properties. All seven kana blocks
are complete. The four CJK-encoded kana ligatures and the two Minnan combining
marks are checked separately. The reproducible audit is in
[kana-coverage-0.112.json](kana-coverage-0.112.json).

The last gap was **㌬ U+332C SQUARE PAATU**, decomposed as パーツ. Unicode describes
this as an unused erroneous representation originally intended for the Thai
baht symbol. It is included for encoding coverage. See the
[Unicode CJK Compatibility chart](https://www.unicode.org/charts/PDF/U3300.pdf).

Its horizontal form uses PA and the prolonged sound mark from Noto Serif JP's
㌫ U+332B SQUARE PAASENTO, followed by TSU from ㌪ U+332A SQUARE HAITU. The vertical
form uses the corresponding native vertical components, read down the right
column and then the left. Stroke proportions are preserved; no whole-character
compression is applied. Both forms retain a 1,000-unit advance.

`scripts/check_coverage.py` reads the checksum-pinned Unicode properties and
fails if any required character is absent. This establishes encoded character
coverage; it does not establish every manuscript variant or arbitrary
combining-mark sequence. Regular remains the only weight.
