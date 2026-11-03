"""The temporary language tool for players (until an official Arabic release exists), split in two on purpose:
the mod portal rejects executable files in a mod ("Please remove all files ending in exe, bat, ps1, sh, py").
- the mod carries data only: <mod>/scenario-patch/ (patched tutorial/scenario texts) and README-AR.txt;
- the scripts go to download/arabic-tools.zip, served from GitHub (link in the README and the portal description).
Player mode of FactorioArabic.psm1 reads scenario-patch from the installed mod, so the patch always matches the mod."""
import shutil, zipfile
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


def executables(zip_path: Path) -> list:
    with zipfile.ZipFile(zip_path) as z:
        return [n for n in z.namelist() if n.lower().endswith(EXECUTABLE)]
