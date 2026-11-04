"""The temporary language tool for players (until an official Arabic release exists), split in two on purpose:
the mod portal rejects executable files in a mod ("Please remove all files ending in exe, bat, ps1, sh, py").
- the mod carries data only: <mod>/scenario-patch/ (patched tutorial/scenario texts) and README-AR.txt;
- the scripts go to download/arabic-tools.zip, served from GitHub (link in the README and the portal description).
Player mode of FactorioArabic.psm1 reads scenario-patch from the installed mod, so the patch always matches the mod."""
import re, shutil, zipfile
from pathlib import Path
from tools import scenarios
from tools.paths import ROOT

README = ROOT / 'mod' / 'README-AR.txt'
TOOL_FILES = {  # name inside arabic-tools.zip -> source
    'Change-Language.cmd': ROOT / 'Change-Language.cmd',
    'Change-Language.ps1': ROOT / 'Change-Language.ps1',
    'FactorioArabic.psm1': ROOT / 'tools' / 'FactorioArabic.psm1',
    'README-AR.txt': README,
}
TOOL_ZIP = ROOT / 'download' / 'arabic-tools.zip'
EXECUTABLE = ('.exe', '.bat', '.cmd', '.ps1', '.psm1', '.sh', '.py')   # never inside the mod zip
FIXED_TIME = (2026, 1, 1, 0, 0, 0)   # same bytes for same content: the tracked zip only changes when a file does


def build_scenarios():
    scenarios.build(allow_missing=True)


def add_scenario_patch(mod_dir: Path) -> Path:
    build_scenarios()
    mod = Path(mod_dir)
    patch = mod / 'scenario-patch'   # not 'scenarios/': that folder would load as a mod scenario
    if patch.exists():
        shutil.rmtree(patch)  # build output only
    shutil.copytree(scenarios.OUT_SC, patch)
    shutil.copy2(README, mod / 'README-AR.txt')
    return patch


def tool_zip(out: Path = TOOL_ZIP) -> Path:
    """Files at the zip root: Windows "Extract All" then makes one arabic-tools folder, not two nested ones."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, src in TOOL_FILES.items():
            z.writestr(zipfile.ZipInfo(name, FIXED_TIME), src.read_bytes(), zipfile.ZIP_DEFLATED)
    return out


def tools_version() -> str:
    """The number both tool zips show (FactorioArabic.psm1) and their GitHub release tag: translator-<version>."""
    text = TOOL_FILES['FactorioArabic.psm1'].read_text(encoding='ascii')
    return re.search(r"^\$script:ToolsVersion = '(\d+\.\d+\.\d+)'", text, re.M).group(1)


def executables(zip_path: Path) -> list:
    with zipfile.ZipFile(zip_path) as z:
        return [n for n in z.namelist() if n.lower().endswith(EXECUTABLE)]


# ---------- the mods translator for players: a GitHub release asset, never tracked (about 13 MB) ----------
TRANSLATOR_ZIP = ROOT / 'dist' / 'arabic-mods-translator.zip'
TRANSLATOR_FILES = {**TOOL_FILES,
                    'Translate-Mods.cmd': ROOT / 'Translate-Mods.cmd',
                    'Translate-Mods.ps1': ROOT / 'Translate-Mods.ps1'}
ENGINE = ['__init__', 'modpack', 'translator', 'memory', 'build', 'metrics', 'cfg', 'corrections', 'plurals', 'lint',
          'paths', 'textfx']   # tools.modpack and everything it imports
PTH = 'python313.zip\n.\n..\\app\nLib\\site-packages\n'   # embedded Python ignores PYTHONPATH: its ._pth is the path


def translator_zip(out: Path = TRANSLATOR_ZIP) -> Path:
    """Launcher + engine (app/tools) + embedded Python with arabic_reshaper and fontTools: no installation needed."""
    from tools import vendor
    files = vendor.ensure()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, src in TRANSLATOR_FILES.items():
            z.writestr(zipfile.ZipInfo(name, FIXED_TIME), src.read_bytes(), zipfile.ZIP_DEFLATED)
        for m in ENGINE:
            z.writestr(zipfile.ZipInfo(f'app/tools/{m}.py', FIXED_TIME), (ROOT / 'tools' / f'{m}.py').read_bytes(),
                       zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo('app/glossary.json', FIXED_TIME), (ROOT / 'glossary.json').read_bytes(), zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(files['python-3.13.14-embed-amd64.zip']) as py:
            for info in py.infolist():
                data = PTH.encode() if info.filename == 'python313._pth' else py.read(info)
                z.writestr(zipfile.ZipInfo(f'python/{info.filename}', FIXED_TIME), data, zipfile.ZIP_DEFLATED)
        for wheel in ('arabic_reshaper-3.0.1-py3-none-any.whl', 'fonttools-4.68.0-py3-none-any.whl'):
            with zipfile.ZipFile(files[wheel]) as w:   # a pure-Python wheel is installed by unpacking it
                for info in w.infolist():
                    if not info.is_dir():
                        z.writestr(zipfile.ZipInfo(f'python/Lib/site-packages/{info.filename}', FIXED_TIME),
                                   w.read(info), zipfile.ZIP_DEFLATED)
    return out


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['translator']:
        p = translator_zip()
        print(p, p.stat().st_size // 1024, 'KB')
    elif sys.argv[1:] == ['version']:
        print(tools_version())   # the release tag is translator-<this>
    else:
        sys.exit('usage: python -E -m tools.bundle translator | version')
