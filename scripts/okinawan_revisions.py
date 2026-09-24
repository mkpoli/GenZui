"""Build the Okinawan letters at earlier revisions.

Each revision is built in a throwaway worktree that shares this checkout's
downloaded sources, so the study page can show the same letter at every step
of its design. Both the fonts and the manifest stay in the ignored build
output; nothing here is packaged with GenZui.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from sources import ROOT

FONTS = ROOT/'build/okinawan/fonts'
STEM = Path('build/serif/GenZuiSerif-Regular.woff2')


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def serif(cwd):
    subprocess.run([sys.executable, 'scripts/serif.py'], cwd=cwd, check=True, capture_output=True)


def build(revisions):
    FONTS.mkdir(parents=True, exist_ok=True)
    made = []
    for spec in revisions:
        ref, _, label = spec.partition('=')
        key = 'rev-' + git('rev-parse', '--short', ref)
        label = label or f'{key[4:]} {git("log", "-1", "--format=%s", ref)}'
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)/'tree'
            git('worktree', 'add', '--detach', str(tree), ref)
            try:
                for source in (ROOT/'sources/upstream').glob('*/*'):
                    if source.suffix in ('.ttf', '.otf'):
                        target = tree/'sources/upstream'/source.parent.name/source.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.symlink_to(source)
                (tree/'data/unicode').mkdir(parents=True, exist_ok=True)
                for source in (ROOT/'data/unicode').glob('*'):
                    (tree/'data/unicode'/source.name).symlink_to(source)
                serif(tree)
                shutil.copyfile(tree/STEM, FONTS/(key+'.woff2'))
            finally:
                git('worktree', 'remove', '--force', str(tree))
        made.append({'key': key, 'label': label})
    # Leave the ordinary build in place for the rest of the page and the checks.
    serif(ROOT)
    shutil.copyfile(ROOT/STEM, FONTS/'genzui.woff2')
    made.append({'key': 'genzui', 'label': 'working tree'})
    (FONTS/'revisions.json').write_text(json.dumps(made, ensure_ascii=False, indent=2)+'\n')
    print('Revisions: ' + ', '.join(r['key'] for r in made))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('revisions', nargs='*', help='commits to build, oldest first, as ref or ref=label')
    args = parser.parse_args()
    build(args.revisions)
