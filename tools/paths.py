import os
from functools import lru_cache
from pathlib import Path

GAME_DATA = Path(os.environ.get('FACTORIO_DATA', r'C:\Program Files (x86)\Steam\steamapps\common\Factorio\data'))
GAME_EXE = GAME_DATA.parent / 'bin' / 'x64' / 'factorio.exe'
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'ar'
WORK = ROOT / 'work'
DIST = ROOT / 'dist'
REPORTS = ROOT / 'reports'
MODULES = ['core', 'base', 'elevated-rails', 'quality', 'recycler', 'space-age']


@lru_cache(maxsize=None)
def read_en(module: str) -> dict[str, str]:
    from tools.cfg import read_cfg
    return read_cfg(GAME_DATA / module / 'locale' / 'en' / f'{module}.cfg')
