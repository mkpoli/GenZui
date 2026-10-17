# GenZui Serif 0.106

KOTO uses accepted candidate E. WU’s curved descent is now the default;
`ss01` is named **Hooked WU** and selects the revised hooked form. Both forms
remain U+1B11F. Existing text with `ss01` enabled will therefore show the hook.

| Form | Construction |
| --- | --- |
| KOTO U+1B123 | Exact candidate E outline, including the lower upper curve, leftward shift and extended rising right stroke. |
| WU U+1B11F | The former curved alternate is unchanged. The hooked stem bows farther right while retaining its 62-unit width at y=250 and its low return. |
| TOMO U+2A708 | Native モ shoulder and lower return; only the intervening shaft is lengthened. The shared 92% optical reduction remains. |
| Katakana NARI U+2CEFF | A shallower lower turn and broad, low sweep, informed by the 1899 specimen. The separate native シ stroke remains. |
| Hiragana NARI U+2CF02 | Native ん brush entry, diagonal and rounded foot meet a drawn low wave. The bottom remains at −32. |
| SHITE U+2CF00 | The native シ middle dot is enlarged to 114% and overlaps the ノ-derived stroke directly. |
| Alternate NE U+1B127 | A lighter fold-back and changing top-bar thickness; the lower crossbar remains in place. |
| Alternate WI U+1B128 | A straighter lower descent and reduced thickness around its centreline. |

TOKI, TOTE and YORI retain their accepted outlines. KOTO, TOKI, TOTE and YORI
appear once in the gallery. The WU selector compares matching forms across
versions despite the reversal of `ss01`; the unchanged curved form appears once.
All specimens retain horizontal and vertical context. Swapping versions changes
the outline and both reading samples, including when the fallback userscript runs.

## References

The [1899 操觚便覧 specimen](https://dl.ndl.go.jp/pid/863176/1/12), p. 16,
shows katakana NARI with a shallow lower sweep. The
[1902 和漢の文典 specimen](https://dl.ndl.go.jp/pid/864212/1/36), p. 60,
shows a swept entry and low wave in hiragana NARI. The latter has shorter
proportions than the Japanese JMJ-056850 form in the
[Unicode Extension F chart](https://www.unicode.org/charts/PDF/Unicode-18.0/U180-2CEB0.pdf).
GenZui keeps that reference’s long diagonal and uses native ん stroke treatment.
The scans inform structure; no printed contours were traced into the font.

The two public-domain NDL crops are included under each NARI card’s references.
Their source and crop coordinates are recorded in [specimens/README.md](specimens/README.md).

## Verification

The build checks compare KOTO with the preserved candidate E, confirm that the
new default WU equals the former alternate, and protect the accepted TOKI/TOTE/YORI.
They also check small-size connectivity, mark placement, vertical metrics and
the TOMO top junction against its native モ bar. Font and browser reports record
the hashes of the tested files.
