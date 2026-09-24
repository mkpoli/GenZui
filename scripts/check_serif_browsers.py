"""Check the built GenZui Serif faces in Windows headless Chrome, Vivaldi and Firefox.

Runs from WSL. Chrome and Vivaldi are driven over the DevTools protocol and
Firefox over Marionette, each with an isolated profile in a staged folder
under the Windows temp directory. Browser paths come from a JSON registry
(default ~/.config/genzui/windows-browsers.json) of the form
{"chrome.exe": {"path": "C:\\\\...\\\\chrome.exe"}, "vivaldi.exe": {...}, "firefox.exe": {...}}.
Writes build/serif/browser-checks.json, which package_serif.py requires.
"""
import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from serif import OUT, STEM, VERSION
from sources import ROOT

HERE = Path(__file__).resolve().parent
FORMATS = {'ttf': 'truetype', 'woff2': 'woff2'}
MIXED = '日本語の文に𛀁𛄟𛄠と「ゐゑヰヱ」を交へ、Latin 0.114と数字123。'
MARKS = ['𛄟\u3099', 'チウ\u0305', '𛀁\u3099', 'セ\u309a', 'ヰ\u3099']


def q(value):
    return "'" + value.replace("'", "''") + "'"


def redact(text):
    text = re.sub(r'/home/[^/\s]+', '~', text)
    text = re.sub(r'(?i)(/mnt/c/Users|[A-Z]:[\\/]+Users)[\\/]+[^\\/\s\'"]+', '~', text)
    return text


def faces():
    """(style, weight, stem) for each built face; Regular is required."""
    found = [('Regular', 400, STEM)]
    if (OUT/'GenZuiSerif-Bold.ttf').exists():
        assert (OUT/'GenZuiSerif-Bold.woff2').exists(), 'GenZuiSerif-Bold.woff2 is missing.'
        found.append(('Bold', 700, 'GenZuiSerif-Bold'))
    return found


def targets():
    historical = [r['character'] for r in json.loads((ROOT/'research/repertoire.json').read_text())['characters']]
    okinawan = [''.join(chr(int(cp, 16)) for cp in e['output'])
                for e in json.loads((ROOT/'data/okinawan/mappings.json').read_text())['characters']]
    return historical, okinawan


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_dir(prefix):
    temp = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', '[IO.Path]::GetTempPath()'], text=True).strip()
    win = temp.rstrip('\\') + '\\' + prefix + '-' + uuid.uuid4().hex[:8]
    stage = Path(subprocess.check_output(['wslpath', '-u', win], text=True).strip())
    stage.mkdir()
    return win, stage


def stage_fonts(stage, face_list):
    """Copy the faces and return their staged hashes, which are the bytes under test."""
    hashes = {}
    for style, _, stem in face_list:
        for ext in FORMATS:
            shutil.copy2(OUT/f'{stem}.{ext}', stage/f'{stem}.{ext}')
            hashes[(style, ext)] = sha256(stage/f'{stem}.{ext}')
    return hashes


def run(win, stage, template, timeout, **tokens):
    script = (HERE/'browser'/template).read_text()
    for key, value in tokens.items():
        script = script.replace(f'__{key}__', value)
    assert '__' not in re.sub(r'__(proto|dirname)__', '', script), 'Unfilled template token'
    (stage/'check.ps1').write_text(script, encoding='utf-8-sig')
    r = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', win + '\\check.ps1'],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(redact(r.stdout + r.stderr))
    remaining(win)
    return json.loads((stage/'report.json').read_text(encoding='utf-8-sig'))


def remaining(win):
    """Fail if any process still names the stage folder. The path is passed encoded so this query does not match itself."""
    encoded = base64.b64encode(win.encode()).decode()
    count = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
        f"$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}'));"
        "@(Get-CimInstance Win32_Process|Where-Object {$_.CommandLine -and $_.CommandLine.Contains($p)}).Count"], text=True).strip()
    assert count == '0', f'{count} browser processes remain for the test profile'


def file_url(win, name):
    return 'file:///' + win.replace('\\', '/') + '/' + name


def chromium_page(face_list, historical, okinawan):
    rules = ''.join(f'@font-face{{font-family:GZ{ext};src:url({stem}.{ext}) format("{fmt}");font-weight:{weight}}}'
                    for ext, fmt in FORMATS.items() for _, weight, stem in face_list)
    texts = {'mixed': MIXED, 'vertical': MIXED + ''.join(historical[:40]), 'marks': ' '.join(MARKS),
             'historical': ''.join(historical), 'okinawan': ' '.join(okinawan)}
    probes = ''.join(
        f'<div id="{ext}-{weight}-{kind}" data-probe class="{"v" if kind == "vertical" else "h"}" '
        f'style="font:{weight} 24px/1.6 GZ{ext}">{html.escape(text)}</div>'
        for ext in FORMATS for _, weight, _ in face_list for kind, text in texts.items())
    return ('<!doctype html><meta charset="utf-8"><title>GenZui Serif browser check</title>'
            f'<style>{rules}body{{margin:16px}}.h{{width:1400px;overflow-wrap:anywhere;margin:0 0 12px}}'
            f'.v{{writing-mode:vertical-rl;height:480px;margin:0 0 12px}}</style>{probes}')


def chromium(name, binary, face_list, historical, okinawan):
    win, stage = stage_dir('genzui-serif-' + name)
    try:
        hashes = stage_fonts(stage, face_list)
        (stage/'proof.html').write_text(chromium_page(face_list, historical, okinawan), encoding='utf-8')
        data = run(win, stage, 'serif-chromium.ps1', 180, ROOT=q(win), BINARY=q(binary),
                   EXTRA="'--disable-vivaldi'," if name == 'vivaldi' else '', PAGE=q(file_url(win, 'proof.html')))
        expected = len(FORMATS) * len(face_list)
        assert len(data['fontFaces']) == expected and all(f['status'] == 'loaded' for f in data['fontFaces']), (name, data['fontFaces'])
        assert 'OTS parsing error' not in (stage/'stderr.txt').read_text(encoding='utf-8-sig', errors='replace'), name
        details = {}
        for style, weight, stem in face_list:
            fonts = {k: v for k, v in data['fonts'].items() if k.split('-')[1] == str(weight)}
            assert len(fonts) == len(FORMATS) * 5, (name, style, sorted(fonts))
            for probe, used in fonts.items():
                assert len(used) == 1 and used[0]['postScriptName'] == stem and used[0]['isCustomFont'], (name, probe, used)
            details[style] = {'weight': weight, 'ttf_sha256': hashes[(style, 'ttf')], 'woff2_sha256': hashes[(style, 'woff2')],
                              'actual_fonts': fonts}
        return {'browser': name, 'version': data['version'].split('/', 1)[-1], 'cdp_product': data['version'],
                'font_faces': data['fontFaces'], 'faces': details,
                'ots_error': False, 'owned_processes_stopped': True, 'status': 'passed'}, hashes
    finally:
        shutil.rmtree(stage)


FIREFOX_CHECK = '''var done=arguments[arguments.length-1];(async()=>{
const faces=FACES, points=POINTS;
for(const f of faces)for(const ext of ['ttf','woff2']){const face=new FontFace(f.style+ext,'url('+f.stem+'.'+ext+')',{weight:String(f.weight)});document.fonts.add(face);await face.load();}
await document.fonts.ready;
const fonts=[...document.fonts].map(f=>({family:f.family,weight:f.weight,status:f.status}));
if(fonts.some(f=>f.status!=='loaded'))throw new Error('Font not loaded: '+JSON.stringify(fonts));
const c=document.createElement('canvas');c.width=480;c.height=120;const ctx=c.getContext('2d');
function render(font,s){ctx.clearRect(0,0,c.width,c.height);ctx.font=font;ctx.fillText(s,16,84);return c.toDataURL()}
const faceResults={};
for(const f of faces){
 for(const s of points){if(render(f.weight+' 64px '+f.style+'ttf',s)!==render(f.weight+' 64px '+f.style+'woff2',s))throw new Error(f.style+' TTF and WOFF2 differ for U+'+[...s].map(x=>x.codePointAt(0).toString(16).toUpperCase()).join(' U+'));}
 faceResults[f.style]={weight:f.weight,target_count:points.length,raster_equivalence:true};
}
return {status:'passed',fonts,faces:faceResults};})().then(done).catch(e=>done({failure:e.message}));'''


def firefox(binary, face_list, historical, okinawan):
    win, stage = stage_dir('genzui-serif-firefox')
    try:
        hashes = stage_fonts(stage, face_list)
        (stage/'proof.html').write_text('<!doctype html><meta charset="utf-8"><title>GenZui Serif browser check</title>', encoding='utf-8')
        points = historical + okinawan
        js = (FIREFOX_CHECK.replace('FACES', json.dumps([{'style': s, 'weight': w, 'stem': t} for s, w, t in face_list]))
              .replace('POINTS', json.dumps(points, ensure_ascii=False)))
        data = run(win, stage, 'serif-firefox.ps1', 300, ROOT=q(win), BINARY=q(binary),
                   PAGE=q(file_url(win, 'proof.html')), CHECK=q(js))
        result = data['result']
        assert result['status'] == 'passed' and len(result['fonts']) == len(FORMATS) * len(face_list), result['fonts']
        assert all(f['status'] == 'loaded' for f in result['fonts']), result['fonts']
        details = {style: {**result['faces'][style], 'ttf_sha256': hashes[(style, 'ttf')], 'woff2_sha256': hashes[(style, 'woff2')]}
                   for style, _, _ in face_list}
        return {'browser': 'firefox', 'version': data['version'], 'font_faces': result['fonts'], 'faces': details,
                'owned_processes_stopped': True, 'status': 'passed'}, hashes
    finally:
        shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--browsers', type=Path, default=Path.home()/'.config/genzui/windows-browsers.json')
    args = parser.parse_args()
    registry = json.loads(args.browsers.read_text(encoding='utf-8-sig'))
    face_list = faces()
    checks = json.loads((OUT/'checks.json').read_text())
    hashes = {ext + '_sha256': sha256(OUT/f'{STEM}.{ext}') for ext in FORMATS}
    assert checks['status'] == 'passed' and all(checks[k] == v for k, v in hashes.items()), \
        'Run check_serif.py on the current build first.'
    if len(face_list) > 1:
        hashes.update({f'bold_{ext}_sha256': sha256(OUT/f'GenZuiSerif-Bold.{ext}') for ext in FORMATS})
    historical, okinawan = targets()
    results = []
    for name in ('chrome', 'vivaldi', 'firefox'):
        binary = registry[name + '.exe']['path']
        if name == 'firefox':
            result, staged = firefox(binary, face_list, historical, okinawan)
        else:
            result, staged = chromium(name, binary, face_list, historical, okinawan)
        tested = {(f'bold_{ext}' if style == 'Bold' else ext) + '_sha256': v for (style, ext), v in staged.items()}
        assert tested == hashes, f'{name} tested different font bytes'
        results.append(result)
        print(f"{name} {result['version']}: {', '.join(style for style, _, _ in face_list)} passed.", flush=True)
    report = {'version': VERSION,
              'method': 'Windows headless Chrome, Vivaldi and Firefox with isolated profiles; '
                        'Chrome and Vivaldi confirm with CSS.getPlatformFontsForNode that mixed, vertical, mark, '
                        f'all {len(historical)} historical and all {len(okinawan)} Okinawan strings use the GenZui face alone '
                        'from both TTF and WOFF2, and Firefox requires identical canvas rasters from TTF and WOFF2 for every target.',
              **hashes, 'results': results}
    (OUT/'browser-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Saved {OUT.relative_to(ROOT)}/browser-checks.json')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:  # Paths in browser errors can name the Windows user.
        sys.exit(redact(f'{type(error).__name__}: {error}'))
