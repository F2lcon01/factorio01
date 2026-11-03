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
    checked, bad = 0, []
    for dump in (ENV / 'write' / 'script-output').glob('*-locale.json'):
        ptype = dump.name[:-len('-locale.json')]
        data = json.loads(dump.read_text(encoding='utf-8'))
        for kind, section in (('names', f'{ptype}-name'), ('descriptions', f'{ptype}-description')):
            for proto, got in data.get(kind, {}).items():
                exp = built.get(f'{section}/{proto}')
                if exp is None or '__' in exp:
                    continue  # not ours, or contains runtime-resolved parameters
                checked += 1
                if got != exp.replace('\\n', '\n'):
                    bad.append(f'| {section}/{proto} | {got[:60]} |')
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'verify-game.md').write_text(
        f'checked={checked} mismatched={len(bad)}\n\n| key | game shows |\n|---|---|\n' + '\n'.join(bad[:200]) + '\n',
        encoding='utf-8')
    print(f'checked={checked} mismatched={len(bad)}')
    sys.exit(1 if bad or checked == 0 else 0)


if __name__ == '__main__':
    main(*sys.argv[1:])
