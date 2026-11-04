"""The game's own core texts (shown before any mod loads, e.g. "Error loading mods") are replaced by the mod's shaped
core.cfg, the original kept. Runs the player-mode module in Windows PowerShell 5.1 on a copy of the game's layout."""
import json, os, shutil, subprocess
import pytest
from tools.paths import ROOT

PS = shutil.which('powershell')
pytestmark = pytest.mark.skipif(not PS, reason='Windows PowerShell not found')
REVERSED = 'title=تاليدعتلا ليمحت يف أطخ\n'          # what the game ships: reversed letters, unshaped
SHAPED = 'title=ﺕﻼﻳﺪﻌﺘﻟﺍ ﻞﻴﻤﺤﺗ ﻲﻓ ﺄﻄﺧ\n'          # what the mod ships: presentation forms, engine order


def _layout(tmp_path):
    game, user = tmp_path / 'Factorio', tmp_path / 'AppData'
    (game / 'data' / 'base').mkdir(parents=True)
    (game / 'data' / 'base' / 'info.json').write_text(json.dumps({'version': '2.1.24'}))
    core = game / 'data' / 'core' / 'locale' / 'ar'
    core.mkdir(parents=True)
    (core / 'core.cfg').write_text('[gui-mod-load-error]\n' + REVERSED, encoding='utf-8')
    (core / 'info.json').write_text(json.dumps({'language-name': 'x'}), encoding='utf-8')
    mods = user / 'Factorio' / 'mods'
    mod = mods / 'arabic-complete_2.1.24'
    (mod / 'locale' / 'ar').mkdir(parents=True)
    (mod / 'info.json').write_text(json.dumps({'name': 'arabic-complete', 'version': '2.1.24', 'factorio_version': '2.1'}))
    (mod / 'locale' / 'ar' / 'core.cfg').write_text('[gui-mod-load-error]\n' + SHAPED, encoding='utf-8')
    (mods / 'mod-list.json').write_text(json.dumps({'mods': [{'name': 'arabic-complete', 'enabled': True}]}))
    (user / 'Factorio' / 'config').mkdir(parents=True)
    (user / 'Factorio' / 'config' / 'config.ini').write_text('[general]\nlocale=ar\n', encoding='utf-8')
    tools = tmp_path / 'arabic-tools'   # player layout: no tools\autoupdate.py next to it
    tools.mkdir()
    shutil.copy(ROOT / 'tools' / 'FactorioArabic.psm1', tools)
    return game, user, tools / 'FactorioArabic.psm1', core / 'core.cfg', mod / 'locale' / 'ar' / 'core.cfg'


def _ps(module, game, user, script):
    cmd = (f"$ErrorActionPreference = 'Stop'; $env:FA_FACTORIO_DIR = '{game}'; Import-Module '{module}' -Force; "
           f"Set-FAUserAppData '{user}'; {script}")
    # PowerShell 7's PSModulePath, inherited when pytest runs under pwsh, hides Windows PowerShell's own modules
    # (Get-FileHash): players start the tool from Explorer and never have it
    env = {k: v for k, v in os.environ.items() if k.upper() != 'PSMODULEPATH'}
    r = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout.split()


def test_the_error_screen_texts_are_patched_and_the_original_is_kept(tmp_path):
    game, user, module, game_cfg, mod_cfg = _layout(tmp_path)
    assert 'core-locale' in _ps(module, game, user, '(Get-FAHealth).Problems')
    assert 'fixed-core' in _ps(module, game, user, 'Invoke-FAFix')
    assert game_cfg.read_bytes() == mod_cfg.read_bytes()
    backup = user / 'Factorio' / 'arabic-tools-backup' / 'core-original-2.1.24' / 'core.cfg'
    assert REVERSED in backup.read_text(encoding='utf-8')                     # Steam's original, kept
    assert 'core-locale' not in _ps(module, game, user, '(Get-FAHealth).Problems')
    game_cfg.write_text('[gui-mod-load-error]\n' + REVERSED + 'new=x\n', encoding='utf-8')   # a Steam update
    assert 'core-locale' in _ps(module, game, user, '(Get-FAHealth).Problems')
    _ps(module, game, user, 'Invoke-FAFix')
    assert REVERSED in backup.read_text(encoding='utf-8') and 'new=x' not in backup.read_text(encoding='utf-8')


def test_english_players_are_not_touched(tmp_path):
    game, user, module, game_cfg, _ = _layout(tmp_path)
    (user / 'Factorio' / 'config' / 'config.ini').write_text('[general]\nlocale=en\n', encoding='utf-8')
    assert 'core-locale' not in _ps(module, game, user, '(Get-FAHealth).Problems')
    assert REVERSED in game_cfg.read_text(encoding='utf-8')
