"""Run factorio --dump-prototype-locale in an isolated env and compare with the built mod."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
from tools.build import build
from tools.cfg import read_cfg
from tools.harness import _assert_valid_ini
from tools.paths import GAME_EXE, REPORTS

ENV = Path(os.environ['TEMP']) / 'fa-verify'
USER_CFG = Path(os.environ['APPDATA']) / 'Factorio' / 'config' / 'config.ini'
BASE_MODS = ['base', 'elevated-rails', 'quality', 'recycler', 'space-age']


def prepare(version):
    if ENV.exists():
        shutil.rmtree(ENV)  # our own temp env only
    (ENV / 'config').mkdir(parents=True); (ENV / 'mods').mkdir(); (ENV / 'write').mkdir()
    cfg = USER_CFG.read_text(encoding='utf-8-sig')
    cfg = re.sub(r'(?m)^write-data=.*$', lambda _: f'write-data={ENV / "write"}', cfg)  # path has backslashes
    cfg = re.sub(r'(?m)^locale=.*$', 'locale=ar', cfg)
    _assert_valid_ini(cfg)
    (ENV / 'config' / 'config.ini').write_text(cfg, encoding='utf-8')
    mod = build(version, out_root=ENV / 'mods')
    mods = [{'name': n, 'enabled': True} for n in BASE_MODS + ['arabic-complete']]
    (ENV / 'mods' / 'mod-list.json').write_text(json.dumps({'mods': mods}), encoding='utf-8')
    return mod


def main(version='0.0.1'):
    sys.stdout.reconfigure(encoding='utf-8')
    mod = prepare(version)
    subprocess.run([str(GAME_EXE), '-c', str(ENV / 'config' / 'config.ini'),
                    '--mod-directory', str(ENV / 'mods'), '--dump-prototype-locale'], check=True, timeout=600)
    if not (ENV / 'write' / 'factorio-current.log').exists():
        sys.exit('isolated write-data was not used; aborting')
    built = {}
    for p in (mod / 'locale' / 'ar').glob('*.cfg'):
        built.update(read_cfg(p))
    # Every name/description the game resolves (incl. composite names such as "__1__ barrel") is classified:
    # exact = equals our key; ok = shaped Arabic built from other keys; english / unshaped = real failures.
    counts, bad = {'exact': 0, 'ok': 0, 'english': 0, 'unshaped': 0}, []
    for dump in (ENV / 'write' / 'script-output').glob('*-locale.json'):
        ptype = dump.name[:-len('-locale.json')]
        data = json.loads(dump.read_text(encoding='utf-8'))
        for kind, section in (('names', f'{ptype}-name'), ('descriptions', f'{ptype}-description')):
            for proto, got in data.get(kind, {}).items():
                exp = built.get(f'{section}/{proto}')
                verdict = 'exact' if exp is not None and got == exp.replace('\\n', '\n') else classify(got)
                counts[verdict] += 1
                if verdict in ('english', 'unshaped'):
                    bad.append(f'| {verdict} | {section}/{proto} | {got[:70]} |')
    REPORTS.mkdir(exist_ok=True)
    summary = ' '.join(f'{k}={v}' for k, v in counts.items())
    (REPORTS / 'verify-game.md').write_text(
        f'{summary}\n\n| verdict | prototype | game shows |\n|---|---|---|\n' + '\n'.join(sorted(bad, reverse=True)) + '\n',
        encoding='utf-8', newline='\n')
    print(summary)
    sys.exit(1 if bad or counts['exact'] == 0 else 0)


def classify(text):
    if any('ء' <= c <= 'ي' and c != 'ـ' for c in text):
        return 'unshaped'  # official (disconnected) Arabic leaked through
    shaped = any('ﭐ' <= c <= '﻿' for c in text)
    if not shaped and re.search(r'[A-Za-z]{3,}', re.sub(r'\[[^\]]*\]', '', text)):
        return 'english'   # fell back to English: key not translated
    return 'ok'


if __name__ == '__main__':
    main(*sys.argv[1:])
