import json
from fontTools.ttLib import TTFont
from tools.build import build
from tools.cfg import read_cfg
from tools.paths import GAME_DATA, MODULES, read_en


def test_mod_structure(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    assert mod.name == 'arabic-complete_9.9.9'
    info = json.loads((mod / 'info.json').read_text(encoding='utf-8'))
    assert info['version'] == '9.9.9' and info['factorio_version'] == '2.1'
    for m in MODULES:
        assert (mod / 'locale' / 'ar' / f'{m}.cfg').exists()


def test_every_output_char_has_a_glyph(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    cmap = set()
    for f in ['NotoSansArabic-Regular', 'NotoSansArabic-Bold', 'NotoSansArabic-SemiBold',
              'TitilliumWeb-Regular', 'NotoSans-Regular', 'DejaVuSans']:
        cmap |= set(TTFont(GAME_DATA / 'core' / 'fonts' / f'{f}.ttf', lazy=True).getBestCmap())
    used = {c for p in (mod / 'locale' / 'ar').glob('*.cfg') for c in p.read_text(encoding='utf-8')}
    missing = sorted(f'U+{ord(c):04X}' for c in used if ord(c) > 0x7F and ord(c) not in cmap)
    assert missing == []


def test_output_has_no_logical_arabic_letters_left(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    for p in (mod / 'locale' / 'ar').glob('*.cfg'):
        for k, v in read_cfg(p).items():
            # U+0640 tatweel (as in \u00AB\u0644\u0640 __1__\u00BB) is a joining stroke with no presentation form by design
            assert not any('\u0621' <= c <= '\u064A' and c != '\u0640' for c in v), (p.name, k)


def test_key_coverage_equals_english(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    for m in MODULES:
        assert read_cfg(mod / 'locale' / 'ar' / f'{m}.cfg').keys() == read_en(m).keys()
