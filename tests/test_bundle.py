import zipfile
from tools import bundle, scenarios
from tools.package import zip_dir


def _fake_patch(tmp_path, monkeypatch):
    out_sc = tmp_path / 'out'
    (out_sc / 'base' / 'scenarios' / 'freeplay' / 'locale').mkdir(parents=True)
    (out_sc / 'base' / 'scenarios' / 'freeplay' / 'locale' / 'freeplay.cfg').write_text('msg-intro=x\n', encoding='utf-8')
    monkeypatch.setattr(scenarios, 'OUT_SC', out_sc)
    monkeypatch.setattr(bundle, 'build_scenarios', lambda: None)   # scenario build is tested elsewhere


def test_mod_carries_data_only(tmp_path, monkeypatch):
    _fake_patch(tmp_path, monkeypatch)
    mod = tmp_path / 'arabic-complete_9.9.9'
    mod.mkdir()
    bundle.add_scenario_patch(mod)
    assert (mod / 'scenario-patch' / 'base' / 'scenarios' / 'freeplay' / 'locale' / 'freeplay.cfg').is_file()
    assert (mod / 'README-AR.txt').is_file()
    assert not (mod / 'scenarios').exists()   # a top-level scenarios/ folder would become a mod scenario
    # regression guard: the mod portal rejects a mod zip with executable files (InvalidModUpload)
    assert bundle.executables(zip_dir(mod, tmp_path / 'mod.zip')) == []


def test_tool_zip_has_the_scripts_at_its_root_and_is_reproducible(tmp_path):
    a = bundle.tool_zip(tmp_path / 'a' / 'arabic-tools.zip')
    b = bundle.tool_zip(tmp_path / 'b' / 'arabic-tools.zip')
    with zipfile.ZipFile(a) as z:
        assert sorted(z.namelist()) == sorted(bundle.TOOL_FILES)
        assert z.read('Change-Language.ps1')[:3] == b'\xef\xbb\xbf'   # BOM for Windows PowerShell 5.1
        assert b'\r\n' in z.read('Change-Language.cmd') and b'\r\n' in z.read('README-AR.txt')
    assert a.read_bytes() == b.read_bytes()
    assert set(bundle.executables(a)) == {'Change-Language.cmd', 'Change-Language.ps1', 'FactorioArabic.psm1'}
