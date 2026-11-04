import json, zipfile
from tools import memory, modpack, translator
from tools.textfx import to_visual


def _mod(root, name, en, ar=None, deps=(), version='1.0.0', lua='', as_zip=False):
    files = {'info.json': json.dumps({'name': name, 'version': version, 'dependencies': list(deps)}),
             'locale/en/strings.cfg': en}
    if ar is not None:
        files['locale/ar/strings.cfg'] = ar
    if lua:
        files['control.lua'] = lua
    top = f'{name}_{version}'
    if as_zip:
        with zipfile.ZipFile(root / f'{top}.zip', 'w') as z:
            for rel, text in files.items():
                z.writestr(f'{top}/{rel}', text)
    else:
        for rel, text in files.items():
            (root / top / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / top / rel).write_text(text, encoding='utf-8')


def _mods_dir(tmp_path, enabled):
    (tmp_path / 'mod-list.json').write_text(json.dumps({'mods': [{'name': n, 'enabled': True} for n in enabled]}))
    return tmp_path


def test_reads_folders_and_zips_and_keeps_the_newest_version(tmp_path):
    _mod(tmp_path, 'alpha', '[alpha]\nx=Old\n', version='1.0.0')
    _mod(tmp_path, 'alpha', '[alpha]\nx=New\n', version='1.2.0', as_zip=True)
    _mod(tmp_path, 'beta', '[beta]\ny=Y\n', as_zip=True)
    mods = {m['name']: m for m in modpack.enabled_mods(_mods_dir(tmp_path, ['alpha', 'beta', 'base']))}
    assert set(mods) == {'alpha', 'beta'}            # base modules are arabic-complete's job
    assert mods['alpha']['locale']['en'] == {'alpha/x': 'New'}


def _info_mod(root, folder, info, en='[s]\nk=Some text\n'):
    (root / folder / 'locale' / 'en').mkdir(parents=True)
    (root / folder / 'info.json').write_text(json.dumps(info))
    (root / folder / 'locale' / 'en' / 's.cfg').write_text(en, encoding='utf-8')


def test_scan_sees_mods_the_game_has_not_listed_yet_and_explains_the_ones_it_will_not_load(tmp_path):
    # mods copied in while the game was closed are not in mod-list.json yet: the game enables them on its next start
    (tmp_path / 'mod-list.json').write_text(json.dumps({'mods': [
        {'name': 'base', 'enabled': True}, {'name': 'space-age', 'enabled': True}, {'name': 'quality', 'enabled': False},
        {'name': 'listed', 'enabled': True}, {'name': 'off', 'enabled': False}]}))
    _info_mod(tmp_path, 'listed_1.0.0', {'name': 'listed', 'version': '1.0.0', 'factorio_version': '2.1'})
    _info_mod(tmp_path, 'Flow Control', {'name': 'Flow Control', 'version': '3.2.4', 'factorio_version': '2.1'})   # no version
    _info_mod(tmp_path, 'old_0.1.4', {'name': 'old', 'version': '0.1.4', 'factorio_version': '0.14'})
    _info_mod(tmp_path, 'off_1.0.0', {'name': 'off', 'version': '1.0.0', 'factorio_version': '2.1'})
    _info_mod(tmp_path, 'needs-lib', {'name': 'needs-lib', 'version': '1.0.0', 'factorio_version': '2.1',
                                      'dependencies': ['base >= 2.1', 'flib >= 0.16', '? optional-thing']})
    _info_mod(tmp_path, 'chain', {'name': 'chain', 'version': '1.0.0', 'factorio_version': '2.1',
                                  'dependencies': ['~ needs-lib']})              # needs a mod that cannot load
    _info_mod(tmp_path, 'dlc', {'name': 'dlc', 'version': '1.0.0', 'factorio_version': '2.1',
                                'dependencies': ['space-age', 'quality']})       # quality is disabled here
    usable, skipped = modpack.scan_mods(tmp_path, '2.1')
    assert sorted(m['name'] for m in usable) == ['Flow Control', 'listed']
    assert {m['name']: m['listed'] for m in usable} == {'Flow Control': False, 'listed': True}
    assert [(s['mod']['name'], s['reason'], s['detail']) for s in skipped] == [
        ('chain', 'missing-dep', 'needs-lib'), ('dlc', 'missing-dep', 'quality'), ('needs-lib', 'missing-dep', 'flib'),
        ('off', 'disabled', ''), ('old', 'incompatible', '0.14')]
    rows = modpack.skipped_states(skipped)
    assert rows[4]['state_ar'] == 'لا يعمل مع إصدار لعبتك' and rows[4]['strings'] == 1


def test_a_provider_at_its_limit_stops_the_run_and_keeps_what_was_done(tmp_path):
    mods = [_m('a', {f'a/k{i}': f'Text number {i}' for i in range(200)})]   # 5 batches of 40
    calls = []

    def limited(batch, terms):
        calls.append(len(batch))
        if len(calls) > 1:
            raise translator.TranslatorError('HTTP 429 (tried 2 times): quota', 429, busy=True)
        return {k: 'نص مترجم رقم ' + k.split('k')[1] for k in batch}, translator.new_usage()
    tm = _tm(tmp_path)
    arabic, _, rows = _resolve(mods, tmp_path, memory_=tm, translate=limited)
    assert len(calls) == 3 and rows['stopped'] is True              # 1 answered, 2 refused, the rest not tried
    assert len(arabic) == 40 and sum(s == 'english' for s in rows['source'].values()) == 160
    assert len(memory.TranslationMemory(tmp_path / 'memory.json')) == 40   # saved as it went, not only at the end


def test_load_order_puts_dependencies_first_and_ignores_incompatible_markers():
    mods = [{'name': n, 'deps': d} for n, d in
            [('zeta', []), ('alpha', ['? zeta >= 1.0']), ('beta', ['! zeta', '~ alpha']), ('gamma', ['(?) beta'])]]
    order = [m['name'] for m in modpack.load_order(mods)]
    assert order.index('zeta') < order.index('alpha')
    assert order.index('beta') < order.index('gamma')
    assert order[0] == 'beta'                         # '!' and '~' do not order; ties go by name


def _tm(tmp_path):
    return memory.TranslationMemory(tmp_path / 'memory.json')


def _resolve(mods, tmp_path, **kw):
    args = dict(base={}, memory_=kw.pop('memory_') if 'memory_' in kw else _tm(tmp_path), overrides={}, terms={},
                translate=None, log=lambda s: None)   # (an empty memory is falsy: never `or` it)
    args.update(kw)
    return modpack.resolve(mods, **args)


def _m(name, en, ar=None, deps=(), version='1'):
    return {'name': name, 'title': name, 'version': version, 'deps': list(deps), 'lua': [],
            'locale': {'en': en, **({'ar': ar} if ar else {})}}


def _fake(answers, calls):
    def translate(batch, terms):
        calls.append(dict(batch))
        u = translator.new_usage()
        u.update(requests=1, input_tokens=100, output_tokens=40, chars_in=400, glossary_chars=40)
        return {k: answers[k] for k in batch if k in answers}, u
    return translate


def test_source_priority_and_validation(tmp_path):
    en = {'s/over': 'Over', 's/mem': 'Cancel', 's/shared': 'Shared text', 's/brand': 'P.U.M.P.',
          's/mt': 'Found __1__ pipes', 's/bad': 'Lost __1__'}
    tm = _tm(tmp_path)
    tm.put('shared TEXT', 'نص مشترك', 'machine')
    calls = []
    arabic, owner, rows = _resolve(
        [_m('m', en)], tmp_path, base={'cancel': 'إلغاء'}, memory_=tm, overrides={'s/over': 'يدوي'},
        translate=_fake({'s/mt': 'وُجد __1__ أنبوب', 's/bad': 'ضاع'}, calls))   # 's/bad' drops __1__: rejected
    assert arabic == {'s/over': 'يدوي', 's/mem': 'إلغاء', 's/shared': 'نص مشترك', 's/mt': 'وُجد __1__ أنبوب'}
    assert rows['source'] == {'s/over': 'override', 's/mem': 'memory-base', 's/shared': 'memory', 's/brand': 'brand',
                              's/mt': 'machine', 's/bad': 'english'}
    assert len(calls) == 2 and set(calls[1]) == {'s/bad'}       # one retry for what failed validation
    assert rows['usage']['requests'] == 2 and rows['usage']['input_tokens'] == 200
    assert tm.get('Found __1__ pipes') == 'وُجد __1__ أنبوب'      # machine results enter the shared memory
    assert tm.get('Over') is None                               # manual overrides never do


def test_second_run_on_the_same_mods_sends_nothing_and_another_mod_reuses_the_memory(tmp_path):
    tm, calls = _tm(tmp_path), []
    answers = {'a/x': 'اختر الوحدات', 'a/y': 'طويل'}
    mods = [_m('a', {'a/x': 'Select modules', 'a/y': 'Long'})]
    _resolve(mods, tmp_path, memory_=tm, translate=_fake(answers, calls))
    assert len(calls) == 1
    arabic, _, rows = _resolve(mods, tmp_path, memory_=tm, translate=_fake(answers, calls))
    assert len(calls) == 1 and rows['usage']['requests'] == 0 and set(arabic) == {'a/x', 'a/y'}
    other = [_m('b', {'b/z': 'select   MODULES'})]                 # same English in another mod: no request either
    arabic, _, rows = _resolve(other, tmp_path, memory_=tm, translate=_fake({}, calls))
    assert len(calls) == 1 and arabic == {'b/z': 'اختر الوحدات'} and rows['source']['b/z'] == 'memory'


def test_reuse_under_another_key_is_listed_for_review_and_quality_checks(tmp_path):
    tm, calls = _tm(tmp_path), []
    _resolve([_m('a', {'a/x': 'Heat pipe', 'a/y': 'Lay the pipe here', 'a/z': 'Echo'})], tmp_path, memory_=tm,
             terms={'pipe': 'أنبوب'},
             translate=_fake({'a/x': 'أنبوب حراري', 'a/y': 'مدّ الخطوط هنا', 'a/z': 'Echo'}, calls))
    arabic, _, rows = _resolve([_m('b', {'b/w': 'Heat pipe'})], tmp_path, memory_=tm)
    assert arabic == {'b/w': 'أنبوب حراري'} and rows['review'] == [('b/w', 'a|a/x')]
    first = _resolve([_m('a', {'a/y': 'Lay the pipe here', 'a/z': 'Echo'})], tmp_path, terms={'pipe': 'أنبوب'},
                     memory_=memory.TranslationMemory(tmp_path / 'fresh.json'),   # resolve saves as it goes
                     translate=_fake({'a/y': 'مدّ الخطوط هنا', 'a/z': 'Echo'}, []))[2]
    assert first['source']['a/z'] == 'english'                 # an answer that copies the English is rejected
    assert first['flags'] == [('a/y', 'مصطلح المسرد لم يُستخدم: pipe ← أنبوب')]


def test_a_mod_kept_original_sends_nothing_and_comes_back_from_the_memory(tmp_path):
    tm, calls = _tm(tmp_path), []
    mods = [_m('a', {'a/x': 'Alpha text'}), _m('b', {'b/y': 'Beta text'})]
    answers = {'a/x': 'نص ألفا', 'b/y': 'نص بيتا'}
    _resolve(mods, tmp_path, memory_=tm, translate=_fake(answers, calls))
    assert len(calls) == 1
    arabic, _, rows = _resolve(mods, tmp_path, memory_=tm, translate=_fake(answers, calls), keep={'a'})
    assert arabic == {'b/y': 'نص بيتا'} and rows['source']['a/x'] == 'original' and len(calls) == 1
    arabic, _, rows = _resolve(mods, tmp_path, memory_=tm, translate=_fake(answers, calls))   # ticked again
    assert arabic == {'a/x': 'نص ألفا', 'b/y': 'نص بيتا'} and len(calls) == 1          # from the memory, no request


def test_a_failed_batch_reports_why_its_strings_stay_english(tmp_path):
    def busy(batch, terms):
        raise translator.TranslatorError('HTTP 503 (tried 4 times): high demand', 503)
    arabic, _, rows = _resolve([_m('a', {'a/x': 'Iron plate'})], tmp_path, translate=busy)
    assert arabic == {} and rows['source']['a/x'] == 'english'
    assert rows['errors'] == ['HTTP 503 (tried 4 times): high demand'] * 2   # first pass and its one retry


def test_a_null_override_keeps_one_string_original(tmp_path):
    calls = []
    arabic, _, rows = _resolve([_m('a', {'a/x': 'Keep English', 'a/y': 'Translate me'})], tmp_path,
                               overrides={'a/x': None}, translate=_fake({'a/y': 'ترجمني'}, calls))
    assert arabic == {'a/y': 'ترجمني'} and rows['source']['a/x'] == 'original' and calls == [{'a/y': 'Translate me'}]


def test_an_updated_mod_only_sends_its_changed_strings(tmp_path):
    tm, calls = _tm(tmp_path), []
    _resolve([_m('a', {'a/x': 'Keep me', 'a/y': 'Old text'})], tmp_path, memory_=tm,
             translate=_fake({'a/x': 'أبقني', 'a/y': 'نص قديم'}, calls))
    _resolve([_m('a', {'a/x': 'Keep me', 'a/y': 'New text'}, version='2')], tmp_path, memory_=tm,
             translate=_fake({'a/y': 'نص جديد'}, calls))
    assert calls[1] == {'a/y': 'New text'}


def test_last_loaded_mod_wins_a_shared_key():
    en, owner, _, conflicts = modpack.merge([_m('a', {'s/k': 'Old text'}), _m('b', {'s/k': 'New text'})])
    assert en == {'s/k': 'New text'} and owner['s/k'] == 'b' and conflicts == [('s/k', 'a', 'b')]


def test_arabic_shipped_by_a_mod_is_used_whatever_its_order(tmp_path):
    base = {'iron plate': 'صفيحة حديدية'}                         # its words make the vocabulary
    logical = 'صفيحة حديدية'
    for shipped in (logical, to_visual(logical, shape=False), to_visual(logical)):   # normal, reversed, pre-shaped
        arabic, _, rows = _resolve([_m('m', {'s/k': 'Plate of iron'}, ar={'s/k': shipped})], tmp_path, base=base)
        assert arabic == {'s/k': logical} and rows['source']['s/k'] == 'mod-arabic', shipped


def test_base_game_keys_are_left_to_arabic_complete(tmp_path):
    calls = []
    arabic, _, rows = _resolve([_m('m', {'item-name/iron-plate': 'Iron sheet'})], tmp_path,
                               translate=_fake({'item-name/iron-plate': 'لوح'}, calls))
    assert rows['en'] == {} and arabic == {} and calls == []


def test_mod_states(tmp_path):
    mods = [_m('new', {'n/a': 'Alpha'}), _m('same', {'s/a': 'Beta'}), _m('upd', {'u/a': 'Gamma'}, version='2'),
            _m('wait', {'w/a': 'Delta'})]
    rows = {'owner': {'n/a': 'new', 's/a': 'same', 'u/a': 'upd', 'w/a': 'wait'},
            'en': {'n/a': 'Alpha', 's/a': 'Beta', 'u/a': 'Gamma', 'w/a': 'Delta'},
            'source': {'n/a': 'machine', 's/a': 'memory', 'u/a': 'memory', 'w/a': 'english'}}
    manifest = {m['name']: {'fp': modpack.mod_fingerprint(m), 'keys': {k: modpack._sha(rows['en'][k])
                                                                      for k in m['locale']['en']}}
                for m in mods if m['name'] in ('same', 'wait')}
    manifest['upd'] = {'fp': 'older', 'keys': {}}
    states = {s['name']: s for s in modpack.mod_states(mods, rows, manifest)}
    assert {n: s['state'] for n, s in states.items()} == {'new': 'new', 'same': 'translated', 'upd': 'changed',
                                                         'wait': 'pending'}
    assert states['upd']['changed'] == 1 and states['wait']['pending'] == 1 and states['same']['state_ar'] == 'مترجم'
    rows['source']['s/a'] = 'original'
    kept = {s['name']: s for s in modpack.mod_states(mods, rows, manifest, keep={'same'})}['same']
    assert kept['state'] == 'original' and kept['excluded'] and kept['arabic'] == 0 and kept['state_ar'] == 'بلغته الأصلية'


def test_savings_are_computed_from_measured_usage():
    rows = {'source': {'a': 'memory', 'b': 'memory-base', 'c': 'machine'},
            'usage': {'input_tokens': 300, 'output_tokens': 100, 'chars_in': 1200, 'glossary_chars': 120}}
    s = modpack.savings(rows, [{'translated': 10, 'input_tokens': 300, 'output_tokens': 100}])
    assert s == {'tokens_per_string': 40.0, 'memory_hits': 2, 'tokens_saved_estimate': 80,
                 'glossary_tokens_this_run': 30}


def test_pack_depends_on_translated_mods_and_holds_only_arabic(tmp_path, monkeypatch):
    monkeypatch.setattr(modpack, 'game_version', lambda: '2.1.24')
    mods = [_m('pump', {'s/a': 'Confirm', 's/b': 'Untranslated'})]
    pack = modpack.build_pack(mods, {'s/a': 'تأكيد'}, {'s/a': 'pump', 's/b': 'pump'}, {}, out_root=tmp_path)
    info = json.loads((pack / 'info.json').read_text(encoding='utf-8'))
    assert info['factorio_version'] == '2.1' and '? pump' in info['dependencies']
    cfg = (pack / 'locale' / 'ar' / 'pump.cfg').read_text(encoding='utf-8')
    assert cfg == f'[s]\na={to_visual("تأكيد")}\n'     # shaped; the untranslated key is left to the game's English


def test_a_mod_name_with_a_space_is_translated_but_not_written_as_a_dependency(tmp_path, monkeypatch):
    monkeypatch.setattr(modpack, 'game_version', lambda: '2.1.24')
    mods = [_m('Flow Control', {'fc/a': 'Valve'}), _m('pump', {'p/a': 'Confirm'})]
    pack = modpack.build_pack(mods, {'fc/a': 'صمام', 'p/a': 'تأكيد'}, {'fc/a': 'Flow Control', 'p/a': 'pump'}, {},
                              out_root=tmp_path)
    deps = json.loads((pack / 'info.json').read_text(encoding='utf-8'))['dependencies']
    assert '? pump' in deps and not any('Flow' in d for d in deps)   # the documented form has no space in a name
    assert (pack / 'locale' / 'ar' / 'Flow Control.cfg').exists()


def test_lua_findings_report_hardcoded_text_and_missing_keys():
    mod = _m('pump', {'failure/no-power-pole': 'x'})
    mod['lua'] = ['f{caption = "Hello world"}', 'return {"failure.no-pole"}', 'x = {"item-name.iron-plate"}']
    found = modpack.lua_findings([mod], {'failure/no-power-pole'})
    assert ('pump', 'hard-coded caption', 'Hello world') in found
    assert ('pump', 'key missing even in English', 'failure.no-pole') in found
    assert not any('iron-plate' in f[2] for f in found)     # base-game sections are not this mod's business
