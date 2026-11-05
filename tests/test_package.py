import zipfile
from tools.package import CHANGELOG_SEP, PENDING, check_changelog, with_pending, zip_dir
from tools.paths import ROOT


def test_project_changelog_is_valid():
    assert check_changelog(ROOT / 'mod' / 'changelog.txt') == []


def test_pending_notes_go_under_the_next_release_once_and_stay_valid(tmp_path):
    log = (ROOT / 'mod' / 'changelog.txt').read_text(encoding='utf-8')
    new = with_pending(log, PENDING.read_text(encoding='utf-8'), '9.9.9', '2026-12-01')
    p = tmp_path / 'changelog.txt'
    p.write_text(new, encoding='utf-8')
    assert check_changelog(p) == [] and new.startswith(f'{CHANGELOG_SEP}\nVersion: 9.9.9\nDate: 2026-12-01\n')
    assert with_pending(new, 'x', '9.9.9', 'd') == new          # that version already has its section
    assert with_pending(log, '\n', '9.9.9', 'd') == log         # nothing pending: unchanged


def test_changelog_checker_catches_bad_indent(tmp_path):
    p = tmp_path / 'c.txt'
    p.write_text(f'{CHANGELOG_SEP}\nVersion: 1.0.0\n Features:\n  - x\n', encoding='utf-8')
    assert len(check_changelog(p)) == 2


def test_zip_has_single_versioned_top_folder(tmp_path):
    src = tmp_path / 'arabic-complete_9.9.9'
    (src / 'locale' / 'ar').mkdir(parents=True)
    (src / 'info.json').write_text('{}', encoding='utf-8')
    (src / 'locale' / 'ar' / 'core.cfg').write_text('[a]\nb=c\n', encoding='utf-8')
    names = zipfile.ZipFile(zip_dir(src, tmp_path / 'x.zip')).namelist()
    assert sorted(names) == ['arabic-complete_9.9.9/info.json', 'arabic-complete_9.9.9/locale/ar/core.cfg']
