from tools import scenarios
from tools.textfx import to_visual


def _fake_game(root):
    loc = root / 'base' / 'scenarios' / 'freeplay' / 'locale'
    (loc / 'en').mkdir(parents=True)
    (loc / 'ar').mkdir(parents=True)
    (loc / 'en' / 'freeplay.cfg').write_text('msg-intro=Welcome.\nmsg-goal=Launch __1__ rockets.\n', encoding='utf-8')
    (loc / 'ar' / 'freeplay.cfg').write_text('msg-intro=' + to_visual('مرحباً.', shape=False) + '\n', encoding='utf-8')
    return loc


def test_import_build_apply_restore_roundtrip(tmp_path, monkeypatch):
    game = tmp_path / 'data'
    loc = _fake_game(game)
    original = (loc / 'ar' / 'freeplay.cfg').read_bytes()
    monkeypatch.setattr(scenarios, 'GAME_DATA', game)
    monkeypatch.setattr(scenarios, 'SRC_SC', tmp_path / 'src')
    monkeypatch.setattr(scenarios, 'OUT_SC', tmp_path / 'out')
    monkeypatch.setattr(scenarios, 'BACKUPS', tmp_path / 'backups')
    monkeypatch.setattr(scenarios, 'TODO', tmp_path / 'todo.jsonl')

    todo = scenarios.import_()
    assert [t['key'] for t in todo] == ['/msg-goal']            # missing key queued
    scenarios.add_translations([{'file': todo[0]['file'], 'key': '/msg-goal', 'ar': 'أطلق __1__ صواريخ.'}])
    scenarios.build()
    scenarios.apply()
    patched = (loc / 'ar' / 'freeplay.cfg').read_text(encoding='utf-8')
    assert 'ﺍ' in patched or any('ﹰ' <= c <= '﻿' for c in patched)  # shaped now
    assert scenarios.status() == {'patched': 1, 'original': 0, 'other': 0}
    scenarios.restore()
    assert (loc / 'ar' / 'freeplay.cfg').read_bytes() == original
    assert scenarios.status() == {'patched': 0, 'original': 1, 'other': 0}


def test_reapply_keeps_the_pristine_original_for_restore(tmp_path, monkeypatch):
    game = tmp_path / 'data'
    loc = _fake_game(game)
    original = (loc / 'ar' / 'freeplay.cfg').read_bytes()
    for name, val in (('GAME_DATA', game), ('SRC_SC', tmp_path / 'src'), ('OUT_SC', tmp_path / 'out'),
                      ('BACKUPS', tmp_path / 'backups'), ('TODO', tmp_path / 'todo.jsonl')):
        monkeypatch.setattr(scenarios, name, val)
    todo = scenarios.import_()
    scenarios.add_translations([{'file': todo[0]['file'], 'key': '/msg-goal', 'ar': 'أطلق __1__ صواريخ.'}])
    scenarios.build(); scenarios.apply()
    scenarios.add_translations([{'file': todo[0]['file'], 'key': '/msg-goal', 'ar': 'أطلق __1__ صاروخاً.'}])
    import time; time.sleep(1.1)  # distinct backup stamp
    scenarios.build(); scenarios.apply()                  # second patch over the first one
    scenarios.restore()
    assert (loc / 'ar' / 'freeplay.cfg').read_bytes() == original


def test_add_translations_rejects_broken_tokens(tmp_path, monkeypatch):
    game = tmp_path / 'data'
    _fake_game(game)
    monkeypatch.setattr(scenarios, 'GAME_DATA', game)
    monkeypatch.setattr(scenarios, 'SRC_SC', tmp_path / 'src')
    monkeypatch.setattr(scenarios, 'TODO', tmp_path / 'todo.jsonl')
    todo = scenarios.import_()
    rejected = scenarios.add_translations([{'file': todo[0]['file'], 'key': '/msg-goal', 'ar': 'أطلق صواريخ.'}])
    assert rejected and 'tokens' in rejected[0]['errors']
