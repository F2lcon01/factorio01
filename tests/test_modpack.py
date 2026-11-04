import json, zipfile
from tools import modpack
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


def test_load_order_puts_dependencies_first_and_ignores_incompatible_markers():
    mods = [{'name': n, 'deps': d} for n, d in
            [('zeta', []), ('alpha', ['? zeta >= 1.0']), ('beta', ['! zeta', '~ alpha']), ('gamma', ['(?) beta'])]]
    order = [m['name'] for m in modpack.load_order(mods)]
    assert order.index('zeta') < order.index('alpha')
    assert order.index('beta') < order.index('gamma')
    assert order[0] == 'beta'                         # '!' and '~' do not order; ties go by name


def _resolve(mods, **kw):
    args = dict(tm={}, vocab=set(), cache={}, overrides={}, glossary={}, translate=None, log=lambda s: None)
    args.update(kw)
    return modpack.resolve(mods, **args)


def _m(name, en, ar=None, deps=()):
    return {'name': name, 'version': '1', 'deps': list(deps), 'lua': [],
            'locale': {'en': en, **({'ar': ar} if ar else {})}}


def test_source_priority_and_validation():
    en = {'s/over': 'Over', 's/cached': 'Cached', 's/mem': 'Cancel', 's/brand': 'P.U.M.P.',
          's/mt': 'Found __1__ pipes', 's/bad': 'Lost __1__'}
    calls = []

    def fake(batch, gloss):
        calls.append(dict(batch))
        return {'s/mt': 'وُجد __1__ أنبوب', 's/bad': 'ضاع'}   # 's/bad' drops __1__: must be rejected
    arabic, owner, rows = _resolve(
        [_m('m', en)], tm={'cancel': 'إلغاء'}, translate=fake,
        overrides={'s/over': 'يدوي'}, cache={'s/cached': {'en': modpack._sha('Cached'), 'ar': 'مخزن', 'src': 'machine'}})
    assert arabic == {'s/over': 'يدوي', 's/cached': 'مخزن', 's/mem': 'إلغاء', 's/mt': 'وُجد __1__ أنبوب'}  # harakat go at shaping
    assert rows['source']['s/brand'] == 'brand' and rows['source']['s/bad'] == 'english'
    assert len(calls) == 2 and set(calls[1]) == {'s/bad'}   # one retry for what failed validation
    assert 'Over' not in calls[0].values() and 'Cancel' not in calls[0].values()


def test_stale_cache_is_retranslated_and_last_loaded_mod_wins():
    cache = {'s/k': {'en': modpack._sha('Old text'), 'ar': 'قديم', 'src': 'machine'}}
    seen = []
    arabic, owner, rows = _resolve([_m('a', {'s/k': 'Old text'}), _m('b', {'s/k': 'New text'})], cache=cache,
                                   translate=lambda b, g: seen.append(b) or {'s/k': 'جديد'})
    assert seen == [{'s/k': 'New text'}] and owner['s/k'] == 'b' and arabic['s/k'] == 'جديد'
    assert rows['conflicts'] == [('s/k', 'a', 'b')]


def test_arabic_shipped_by_a_mod_is_used_whatever_its_order():
    vocab = {'صفيحة', 'حديدية'}
    logical = 'صفيحة حديدية'
    for shipped in (logical, to_visual(logical, shape=False), to_visual(logical)):   # normal, reversed, pre-shaped
        arabic, _, rows = _resolve([_m('m', {'s/k': 'Iron plate'}, ar={'s/k': shipped})], vocab=vocab)
        assert arabic == {'s/k': logical} and rows['source']['s/k'] == 'mod-arabic', shipped


def test_base_game_keys_are_left_to_arabic_complete():
    arabic, _, rows = _resolve([_m('m', {'item-name/iron-plate': 'Iron sheet'})],
                               translate=lambda b, g: {k: 'لوح' for k in b})
    assert rows['en'] == {} and arabic == {}


def test_pack_depends_on_translated_mods_and_holds_only_arabic(tmp_path, monkeypatch):
    monkeypatch.setattr(modpack, 'game_version', lambda: '2.1.24')
    mods = [_m('pump', {'s/a': 'Confirm', 's/b': 'Untranslated'})]
    pack = modpack.build_pack(mods, {'s/a': 'تأكيد'}, {'s/a': 'pump', 's/b': 'pump'}, {}, out_root=tmp_path)
    info = json.loads((pack / 'info.json').read_text(encoding='utf-8'))
    assert info['factorio_version'] == '2.1' and '? pump' in info['dependencies']
    cfg = (pack / 'locale' / 'ar' / 'pump.cfg').read_text(encoding='utf-8')
    assert cfg == f'[s]\na={to_visual("تأكيد")}\n'     # shaped; the untranslated key is left to the game's English


def test_lua_findings_report_hardcoded_text_and_missing_keys():
    mod = _m('pump', {'failure/no-power-pole': 'x'})
    mod['lua'] = ['f{caption = "Hello world"}', 'return {"failure.no-pole"}', 'x = {"item-name.iron-plate"}']
    found = modpack.lua_findings([mod], {'failure/no-power-pole'})
    assert ('pump', 'hard-coded caption', 'Hello world') in found
    assert ('pump', 'key missing even in English', 'failure.no-pole') in found
    assert not any('iron-plate' in f[2] for f in found)     # base-game sections are not this mod's business
