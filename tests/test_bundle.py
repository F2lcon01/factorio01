from tools import bundle, scenarios


def test_add_tools_ships_the_language_tool_and_scenario_patch(tmp_path, monkeypatch):
    out_sc = tmp_path / 'out'
    (out_sc / 'base' / 'scenarios' / 'freeplay' / 'locale').mkdir(parents=True)
    (out_sc / 'base' / 'scenarios' / 'freeplay' / 'locale' / 'freeplay.cfg').write_text('msg-intro=x\n', encoding='utf-8')
    monkeypatch.setattr(scenarios, 'OUT_SC', out_sc)
    monkeypatch.setattr(bundle, 'build_scenarios', lambda: None)   # scenario build is tested elsewhere
    mod = tmp_path / 'arabic-complete_9.9.9'
    mod.mkdir()
    bundle.add_tools(mod)
    t = mod / 'arabic-tools'
    for name in ('Change-Language.cmd', 'Change-Language.ps1', 'FactorioArabic.psm1', 'README-AR.txt'):
        assert (t / name).is_file(), name
    assert (t / 'scenario-patch' / 'base' / 'scenarios' / 'freeplay' / 'locale' / 'freeplay.cfg').is_file()
    assert (t / 'Change-Language.ps1').read_bytes()[:3] == b'\xef\xbb\xbf'   # BOM for Windows PowerShell 5.1
    assert not (mod / 'scenarios').exists()   # a top-level scenarios/ folder would become a mod scenario
