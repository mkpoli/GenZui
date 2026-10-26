"""Package the validated Tangut face, offline specimen, licences and provenance."""

import json
import time
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from tangut_sans import EPOCH, OUT, ROOT, STEM, VERSION, build_hashes, digest

from sources import verify


def package():
    reports = {}
    for filename in ("checks.json", "browser-checks.json"):
        report = json.loads((OUT / filename).read_text())
        reports[filename] = report
        assert report["status"] == "passed", f"Validation failed: {filename}"
        checker = (
            "check_tangut_sans.py"
            if filename == "checks.json"
            else "check_tangut_browser.mjs"
        )
        assert report["checker_sha256"] == digest(ROOT / "scripts" / checker), (
            f"Rerun changed checker: {checker}"
        )
        for ext in ("ttf", "woff2"):
            assert report[ext + "_sha256"] == digest(OUT / (STEM + "." + ext)), (
                f"Stale {filename}; rerun validation."
            )
    assert reports["browser-checks.json"]["specimen_sha256"] == digest(
        OUT / "index.html"
    ), "Rerun browser checks after specimen changes."
    sources = json.loads((OUT / "sources.json").read_text())
    assert not sources["sample"] and sources["version"] == VERSION
    assert sources["scripts_sha256"] == build_hashes()
    assert sources["source_manifest"] == verify(manifest="tangut-manifest.json")
    assert reports["checks.json"]["sources_sha256"] == digest(OUT / "sources.json")
    (OUT / "README.txt").write_text(
        f"GenZui Sans Tangut Regular {VERSION}\n"
        "源萃ゴシック西夏文字\n\n"
        "A development Tangut face with square Gothic terminals.\n"
        "Coverage: 6,145 ideographs, 768 components, U+16FE0, space and NBSP.\n"
        "Coverage follows Noto Serif Tangut 2.168. Later Tangut additions and\n"
        "Components Supplement are absent. Dense joins and small counters need\n"
        "further proofreading; the repertoire has not been proofread in full.\n\n"
        "Install: open GenZuiSansTangut-Regular.ttf and choose Install.\n"
        "Select GenZui Sans Tangut (源萃ゴシック西夏文字) in your application.\n"
        "It is a separate family and can be installed beside GenZui Sans.\n\n"
        "Web: keep the WOFF2 file beside genzui-sans-tangut.css, load that stylesheet,\n"
        'then use font-family: "GenZui Sans", "GenZui Sans Tangut", sans-serif;\n'
        "Offline specimen: open index.html in a browser. The complete-package link\n"
        "on that page refers to the original ZIP and is not needed after extraction.\n\n"
        "Sources (SIL Open Font License 1.1):\n"
        "Noto Serif Tangut 2.168 — character structure and repertoire.\n"
        "https://github.com/notofonts/tangut\n"
        "Noto Sans CJK JP Regular 2.004 — horizontal and vertical stroke outlines.\n"
        "https://github.com/notofonts/noto-cjk/tree/main/Sans\n"
        "GenZui — reconstruction, fitting and spacing.\n"
        "https://github.com/mkpoli/GenZui\n\n"
        "OFL.txt and the two upstream OFL files contain the font licences.\n"
        "NOTICE.txt credits the sources. sources.json records pinned URLs, SHA-256\n"
        "hashes, build-library versions and per-character construction records.\n"
        "checks.json and browser-checks.json record validation of these font files.\n"
    )
    names = [
        STEM + ".ttf",
        STEM + ".woff2",
        "genzui-sans-tangut.css",
        "index.html",
        "NotoSerifTangut-Reference.woff2",
        "OFL.txt",
        "NotoSerifTangut-OFL.txt",
        "NotoSansCJK-OFL.txt",
        "NOTICE.txt",
        "README.txt",
        "sources.json",
        "checks.json",
        "browser-checks.json",
    ]
    archive = OUT / f"GenZuiSansTangut-{VERSION}.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(names):
            info = ZipInfo(name, date_time=time.gmtime(EPOCH)[:6])
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (OUT / name).read_bytes(), compresslevel=9)
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(names)
        for name in names:
            assert z.read(name) == (OUT / name).read_bytes()
    print(f"Wrote {archive.relative_to(ROOT)} ({archive.stat().st_size:,} bytes)")


if __name__ == "__main__":
    package()
