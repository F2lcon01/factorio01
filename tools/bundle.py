"""Ship the language tool inside the mod: <mod>/arabic-tools/ (temporary, until an official Arabic release exists).
Player mode of FactorioArabic.psm1 repairs from arabic-tools/scenario-patch without Python."""
import shutil
from pathlib import Path
from tools import scenarios
from tools.paths import ROOT

FILES = {  # destination name -> source
    'Change-Language.cmd': ROOT / 'Change-Language.cmd',
    'Change-Language.ps1': ROOT / 'Change-Language.ps1',
    'FactorioArabic.psm1': ROOT / 'tools' / 'FactorioArabic.psm1',
    'README-AR.txt': ROOT / 'mod' / 'README-AR.txt',
}


def build_scenarios():
    scenarios.build(allow_missing=True)


def add_tools(mod_dir: Path) -> Path:
    build_scenarios()
    tools = Path(mod_dir) / 'arabic-tools'   # nested on purpose: a top-level scenarios/ would load as a mod scenario
    if tools.exists():
        shutil.rmtree(tools)  # build output only
    tools.mkdir(parents=True)
    for name, src in FILES.items():
        shutil.copy2(src, tools / name)
    shutil.copytree(scenarios.OUT_SC, tools / 'scenario-patch')
    return tools
