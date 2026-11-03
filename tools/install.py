"""Install the built mod into the user's Factorio mods folder, or disable it (never deletes)."""
import json, os, shutil, sys, time
from pathlib import Path
from tools.paths import DIST

FACTORIO = Path(os.environ['APPDATA']) / 'Factorio'
MODS = FACTORIO / 'mods'
PARKED = FACTORIO / 'mods-parked'  # outside mods/: the game would try to load any folder inside it
LIST = MODS / 'mod-list.json'
NAME = 'arabic-complete'


def _stamp():
    return time.strftime('%Y%m%d-%H%M%S')


def _set_enabled(flag: bool):
    shutil.copy(LIST, PARKED / f'mod-list.json.bak-{_stamp()}')
    data = json.loads(LIST.read_text(encoding='utf-8-sig'))
    data['mods'] = [m for m in data['mods'] if m['name'] != NAME] + [{'name': NAME, 'enabled': flag}]
    LIST.write_text(json.dumps(data, indent=2), encoding='utf-8')


def _park_old():
    for old in MODS.glob(f'{NAME}_*'):
        shutil.move(str(old), PARKED / f'{old.name}-{_stamp()}')


def install(version):
    src = DIST / f'{NAME}_{version}'
    PARKED.mkdir(exist_ok=True)
    _park_old()
    shutil.copytree(src, MODS / src.name)
    _set_enabled(True)
    print('installed', src.name, '-> set Settings > Interface > Language = العربية')


def uninstall():
    PARKED.mkdir(exist_ok=True)
    _park_old()
    _set_enabled(False)
    print('disabled; folders parked in', PARKED)


if __name__ == '__main__':
    uninstall() if '--uninstall' in sys.argv else install(sys.argv[1])
