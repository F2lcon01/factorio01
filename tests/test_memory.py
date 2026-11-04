import hashlib
from tools import memory
from tools.textfx import to_visual


def test_exact_then_case_insensitive_and_round_trip(tmp_path):
    tm = memory.TranslationMemory(tmp_path / 'm.json')
    tm.put('  Select   modules ', 'اختر الوحدات', 'machine', 'm1')
    assert tm.get('Select modules') == 'اختر الوحدات'
    assert tm.get('select MODULES') == 'اختر الوحدات'
    assert tm.get('Select module') is None
    tm.save()
    again = memory.TranslationMemory(tmp_path / 'm.json')
    assert len(again) == 1 and again.get('SELECT MODULES') == 'اختر الوحدات'
    assert not (tmp_path / 'm.tmp').exists()                    # atomic write leaves no temp file


def test_legacy_cache_import_keeps_only_entries_that_match_the_english(tmp_path):
    tm = memory.TranslationMemory(tmp_path / 'm.json')
    sha = lambda s: hashlib.sha1(s.encode()).hexdigest()
    cache = {'s/a': {'en': sha('Confirm'), 'ar': 'تأكيد', 'src': 'machine'},
             's/b': {'en': sha('Old'), 'ar': 'قديم', 'src': 'machine'}}
    assert tm.import_legacy_cache(cache, {'s/a': 'Confirm', 's/b': 'New'}) == 1
    assert tm.get('Confirm') == 'تأكيد' and tm.get('New') is None


def test_base_memory_from_an_installed_mod_on_a_players_machine(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, 'SRC', tmp_path / 'no-src')           # player: no project sources
    loc = tmp_path / 'mods' / 'arabic-complete_2.1.24' / 'locale' / 'ar'
    loc.mkdir(parents=True)
    (loc / 'base.cfg').write_text('[item-name]\niron-plate=' + to_visual('صفيحة حديدية') + '\n'
                                  '[fluid-name]\nwater=' + to_visual('ماء') + '\n', encoding='utf-8')
    mem = memory.base_memory(tmp_path / 'mods')
    assert mem['iron plate'] == 'صفيحة حديدية' and mem['water'] == 'ماء'
    assert memory.base_terms(tmp_path / 'mods') == {'iron plate': 'صفيحة حديدية', 'water': 'ماء'}


def test_term_filter_is_word_bounded_longest_first_and_curated_wins():
    tb = memory.term_base({'pipe': 'أنبوب'}, {'pipe': 'ماسورة', 'heat pipe': 'أنبوب حراري', 'ore': 'خام'})
    got = memory.terms_for(['Connect the heat pipe to the PIPE network', 'Explore'], tb)
    assert list(got) == ['heat pipe', 'pipe'] and got['pipe'] == 'أنبوب'   # 'ore' inside 'Explore' is not a hit
