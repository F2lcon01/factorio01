"""Release packaging for mods.factorio.com and the Crowdin hand-off.
python -E -m tools.package 1.0.0
→ mod/thumbnail.png (if missing), dist/arabic-complete_<v>.zip, dist/arabic-crowdin_<v>.zip, reports/crowdin-diff.csv,
  download/arabic-tools.zip (the language tool for GitHub; the mod portal rejects scripts inside a mod)"""
import csv, re, sys, time, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from tools.build import build
from tools.bundle import add_scenario_patch, executables, tool_zip
from tools.cfg import read_cfg
from tools.paths import DIST, GAME_DATA, MODULES, REPORTS, ROOT, read_en
from tools.textfx import from_visual, to_visual

CHANGELOG_SEP = '-' * 99


def thumbnail(path=ROOT / 'mod' / 'thumbnail.png'):
    """144×144, drawn with the game's own Noto Sans Arabic; text pre-shaped like the mod itself."""
    img = Image.new('RGB', (144, 144), (36, 36, 36))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 143, 143], outline=(255, 156, 0), width=4)
    big = ImageFont.truetype(str(GAME_DATA / 'core' / 'fonts' / 'NotoSansArabic-Bold.ttf'), 34)
    small = ImageFont.truetype(str(GAME_DATA / 'core' / 'fonts' / 'TitilliumWeb-Bold.ttf'), 18)
    for text, font, y, color in ((to_visual('العربية'), big, 48, (255, 230, 192)),
                                 ('ARABIC', small, 98, (255, 156, 0))):
        w = d.textlength(text, font=font)
        d.text(((144 - w) / 2, y), text, font=font, fill=color, anchor='lm')
    img.save(path)
    return path


def check_changelog(path):
    """The game's strict changelog format: separator, 'Version: x.y.z', 2-space categories, 4-space entries."""
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    errs = []
    if not lines or lines[0] != CHANGELOG_SEP:
        errs.append('line 1 must be 99 dashes')
    for i, l in enumerate(lines[1:], 2):
        if l == CHANGELOG_SEP or re.fullmatch(r'Version: \d+\.\d+\.\d+', l) or re.fullmatch(r'Date: .+', l) \
                or re.fullmatch(r'  [A-Z][A-Za-z ]+:', l) or re.fullmatch(r'    - .+', l) or re.fullmatch(r'      .+', l):
            continue
        errs.append(f'line {i}: {l!r}')
    return errs


PENDING = ROOT / 'mod' / 'changelog-pending.txt'


def with_pending(changelog: str, pending: str, version: str, date: str) -> str:
    """Notes written between mod releases (tool changes) go under the next release's own version: the portal's
    Changelog tab only changes with a release, and the mod's number follows the game's, so it is not known before."""
    if not pending.strip() or f'\nVersion: {version}\n' in changelog:
        return changelog
    return f'{CHANGELOG_SEP}\nVersion: {version}\nDate: {date}\n{pending.rstrip()}\n' + changelog


def zip_dir(src: Path, out: Path):
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob('*')):
            if f.is_file():
                z.write(f, Path(src.name) / f.relative_to(src))  # top folder = <name>_<version>
    return out


def crowdin_diff(version):
    """Per key: English | official Arabic | ours (both in normal reading order) — for proofreaders."""
    rows, stats = [], {'new': 0, 'changed': 0, 'same': 0}
    for m in MODULES:
        official = read_cfg(GAME_DATA / m / 'locale' / 'ar' / f'{m}.cfg')
        ours = read_cfg(DIST / f'arabic-crowdin_{version}' / 'locale' / 'ar' / f'{m}.cfg')
        for k, e in read_en(m).items():
            o, n = official.get(k), ours.get(k)
            kind = 'new' if o is None else 'same' if o == n else 'changed'
            stats[kind] += 1
            if kind != 'same':
                rows.append([m, k, kind, e, from_visual(o) if o else '', from_visual(n)])
    REPORTS.mkdir(exist_ok=True)
    with open(REPORTS / 'crowdin-diff.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['module', 'key', 'kind', 'english', 'official_arabic', 'proposed_arabic'])
        w.writerows(rows)
    return stats


def main(version):
    sys.stdout.reconfigure(encoding='utf-8')
    if not (ROOT / 'mod' / 'thumbnail.png').exists():
        print('thumbnail:', thumbnail())
    log = ROOT / 'mod' / 'changelog.txt'
    if PENDING.exists():
        text = log.read_text(encoding='utf-8')
        new = with_pending(text, PENDING.read_text(encoding='utf-8'), version, time.strftime('%Y-%m-%d'))
        if new != text:
            log.write_text(new, encoding='utf-8', newline='\n')
            PENDING.write_text('', encoding='utf-8')   # emptied, kept: notes for the release after
            print('changelog: pending notes moved under', version)
    errs = check_changelog(log)
    if errs:
        sys.exit('changelog invalid: ' + '; '.join(errs))
    mod = build(version)
    print('scenario patch:', add_scenario_patch(mod))   # data for the language tool, inside the mod
    crowdin = build(version, shape=False)
    mod_zip = zip_dir(mod, DIST / f'{mod.name}.zip')
    if executables(mod_zip):
        sys.exit(f'mod zip has executable files (the portal rejects them): {executables(mod_zip)}')
    print('mod zip:', mod_zip)
    print('tool zip:', tool_zip())                       # scripts, served from GitHub
    print('crowdin zip:', zip_dir(crowdin, DIST / f'{crowdin.name}.zip'))
    print('crowdin diff:', crowdin_diff(version))


if __name__ == '__main__':
    main(sys.argv[1])
