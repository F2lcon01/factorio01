from tools import scenarios
from tools.build import compat
from tools.import_official import take_official
from tools.textfx import to_visual


def test_compat_follows_the_game_major_minor():
    info = {'factorio_version': '2.1',
            'dependencies': ['base >= 2.1.0', '? space-age >= 2.1.0', '! zzz-arabic-shaper']}
    compat(info, '2.2.7')
    assert info['factorio_version'] == '2.2'
    assert info['dependencies'] == ['base >= 2.2.0', '? space-age >= 2.2.0', '! zzz-arabic-shaper']


def test_take_official_accepts_valid_text_and_rejects_defects():
    en = 'Press __CONTROL__build__.'
    good = to_visual('اضغط __CONTROL__build__.', shape=False)       # how the game stores it
    assert take_official(en, good) == 'اضغط __CONTROL__build__.'
    broken = to_visual('اضغط __CONTROL__بناء__.', shape=False)       # token translated → defective
    assert take_official(en, broken) is None
    assert take_official(en, None) is None
    shaped = to_visual('اضغط __CONTROL__build__.')                   # our own patched file: never re-import
    assert take_official(en, shaped) is None


def _game(root):
    loc = root / 'base' / 'scenarios' / 'freeplay' / 'locale'
    (loc / 'en').mkdir(parents=True)
    (loc / 'ar').mkdir(parents=True)
    (loc / 'en' / 'freeplay.cfg').write_text('msg-intro=Welcome.\nmsg-new=New text.\n', encoding='utf-8')
    (loc / 'ar' / 'freeplay.cfg').write_text('msg-new=' + to_visual('نص جديد.', shape=False) + '\n', encoding='utf-8')
    return loc


def test_scenario_build_after_a_game_update_fills_new_keys(tmp_path, monkeypatch):
    _game(tmp_path / 'data')
    monkeypatch.setattr(scenarios, 'GAME_DATA', tmp_path / 'data')
    monkeypatch.setattr(scenarios, 'SRC_SC', tmp_path / 'src')
    monkeypatch.setattr(scenarios, 'OUT_SC', tmp_path / 'out')
    rel = 'base/scenarios/freeplay/locale/freeplay.cfg'
    (tmp_path / 'src' / rel).parent.mkdir(parents=True)
    (tmp_path / 'src' / rel).write_text('msg-intro=مرحباً.\n', encoding='utf-8')     # our old translation
    try:
        scenarios.build()
        raise AssertionError('strict build must refuse missing keys')
    except SystemExit:
        pass
    scenarios.build(allow_missing=True)
    out = (tmp_path / 'out' / rel).read_text(encoding='utf-8')
    assert 'msg-intro=' in out and 'msg-new=' in out                    # new key taken from the game's Arabic
    assert all('ﭐ' <= c <= '﻿' or not ('ء' <= c <= 'ي') for c in out)  # shaped
