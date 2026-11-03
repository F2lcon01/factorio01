"""Build dist/arabic-complete_<version>/ from src/ar (logical) -> visual shaped locale."""
import json, re, shutil, sys
from pathlib import Path
from tools.cfg import read_cfg, write_cfg
from tools.metrics import line_px
from tools.paths import DIST, GAME_DATA, MODULES, ROOT, SRC, read_en
from tools.textfx import to_visual


def game_version() -> str:
    """Installed game version, e.g. '2.1.24' (data/base/info.json)."""
    return json.loads((GAME_DATA / 'base' / 'info.json').read_text(encoding='utf-8'))['version']


def compat(info: dict, version: str) -> dict:
    """The game disables a mod whose factorio_version (major.minor) differs from its own: follow the game."""
    major_minor = '.'.join(version.split('.')[:2])
    info['factorio_version'] = major_minor
    info['dependencies'] = [re.sub(r'>= \d+\.\d+\.\d+', f'>= {major_minor}.0', d) for d in info['dependencies']]
    return info

WRAP = 460  # tools.metrics.line_px units; calibrated in-game against tooltip_label (reports/spike.md)
WRAP_KEY_RE = re.compile(r'description|tooltip|tips-and-tricks|story|^/')  # multi-line places; '/' = root keys


def visual_value(key: str, logical: str, shape: bool = True) -> str:
    wrap = WRAP if shape and WRAP_KEY_RE.search(key) else None
    return to_visual(logical, shape=shape, wrap=wrap, measure=line_px)


def build(version: str, shape: bool = True, out_root: Path = DIST) -> Path:
    name = 'arabic-complete' if shape else 'arabic-crowdin'
    mod = Path(out_root) / f'{name}_{version}'
    if mod.exists():
        shutil.rmtree(mod)  # build output only, never user data
    loc = mod / 'locale' / 'ar'
    for m in MODULES:
        src = read_cfg(SRC / f'{m}.cfg')
        vis = {k: visual_value(k, v, shape) for k, v in src.items()}
        write_cfg(loc / f'{m}.cfg', vis, list(read_en(m)))
    info = json.loads((ROOT / 'mod' / 'info.json').read_text(encoding='utf-8'))
    info['version'] = version
    compat(info, game_version())
    if not shape:
        info['name'] = name
    (mod / 'info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    shutil.copy(ROOT / 'mod' / 'changelog.txt', mod / 'changelog.txt')
    if shape and (ROOT / 'mod' / 'thumbnail.png').exists():  # shown by the game and the mod portal
        shutil.copy(ROOT / 'mod' / 'thumbnail.png', mod / 'thumbnail.png')
    return mod


if __name__ == '__main__':
    print(build(sys.argv[1], shape='--crowdin' not in sys.argv))
