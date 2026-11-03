"""Headless proof that the game resolves scenario text from the patched files (no window, no Steam relaunch):
factorio --test-scenario base/freeplay with a tiny mod that writes the translated {"msg-intro"} to script-output.
python -E -m tools.scenario_check"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
from tools.cfg import read_cfg
from tools.harness import BASE_MODS, USER_CFG, _assert_valid_ini
from tools.paths import DIST, GAME_EXE

ENV = Path(os.environ['TEMP']) / 'fa-scen'
CONTROL = '''
script.on_event(defines.events.on_tick, function(e)
  if e.tick == 30 then helpers.write_file("fa-scen.txt", {"", {"msg-intro"}})
  elseif e.tick == 90 then script.finish_test(true) end
end)
'''


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if ENV.exists():
        shutil.rmtree(ENV)  # our own temp env only
    for d in ('config', 'mods', 'write'):
        (ENV / d).mkdir(parents=True)
    cfg = USER_CFG.read_text(encoding='utf-8-sig')
    cfg = re.sub(r'(?m)^write-data=.*$', lambda _: f'write-data={ENV / "write"}', cfg)
    cfg = re.sub(r'(?m)^locale=.*$', 'locale=ar', cfg)
    _assert_valid_ini(cfg)
    (ENV / 'config' / 'config.ini').write_text(cfg, encoding='utf-8')
    shutil.copytree(DIST / 'arabic-complete_1.0.0', ENV / 'mods' / 'arabic-complete_1.0.0')
    probe = ENV / 'mods' / 'fa-scen_0.0.1'
    probe.mkdir()
    (probe / 'info.json').write_text(json.dumps({'name': 'fa-scen', 'version': '0.0.1', 'title': 'fa-scen',
                                                 'author': 'Falcon', 'factorio_version': '2.1',
                                                 'dependencies': ['base >= 2.1.0']}), encoding='utf-8')
    (probe / 'control.lua').write_text(CONTROL, encoding='utf-8')
    names = BASE_MODS + ['arabic-complete', 'fa-scen']
    (ENV / 'mods' / 'mod-list.json').write_text(
        json.dumps({'mods': [{'name': n, 'enabled': True} for n in names]}), encoding='utf-8')
    r = subprocess.run([str(GAME_EXE), '-c', str(ENV / 'config' / 'config.ini'), '--mod-directory', str(ENV / 'mods'),
                        '--test-scenario', 'base/freeplay', '--test-ticks', '600'], timeout=600)
    got = (ENV / 'write' / 'script-output' / 'fa-scen.txt').read_text(encoding='utf-8')
    built = read_cfg(DIST / 'scenarios' / 'base' / 'scenarios' / 'freeplay' / 'locale' / 'freeplay.cfg')['/msg-intro']
    ok = got == built.replace('\\n', '\n')
    print(f'exit={r.returncode} matches_patched_build={ok}')
    print('game says:', got[:120])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
