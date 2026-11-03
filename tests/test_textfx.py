from tools.cfg import read_cfg
from tools.paths import GAME_DATA
from tools.textfx import NL, from_visual, to_visual, wrap_logical


def test_sentence_reversed_period_moves_left_digits_kept():
    assert to_visual('بناء 100 جهاز.', shape=False) == '.زاهج 100 ءانب'


def test_parameter_token_atomic():
    assert to_visual('عامل متغير __1__', shape=False) == '__1__ ريغتم لماع'


def test_control_icon_tokens_atomic_and_brackets_mirrored():
    s = 'اضغط __CONTROL__build__ لوضع [item=iron-plate] (الأحمر).'
    assert to_visual(s, shape=False) == '.(رمحألا) [item=iron-plate] عضول __CONTROL__build__ طغضا'


def test_format_tags_stay_in_place_per_segment():
    s = '[font=heading-2]تهانينا![/font][font=default]\\nلقد وصلت.[/font]'
    assert to_visual(s, shape=False) == '[font=heading-2]!انيناهت[/font][font=default]\\n.تلصو دقل[/font]'


def test_plural_forms_reversed_inside_block():
    s = 'لديك __plural_for_parameter__1__{1=عنصر|rest=عناصر}__'
    assert to_visual(s, shape=False) == '__plural_for_parameter__1__{1=رصنع|rest=رصانع}__ كيدل'


def test_shaping_lam_alef_ligature():
    assert to_visual('لا') == '\uFEFB'


def test_harakat_removed_in_output():
    assert to_visual('العَرَبِيَّة') == to_visual('العربية')


def test_involution_unshaped():
    s = 'اضغط __CONTROL__build__ لوضع [item=iron-plate] (الأحمر).'
    assert from_visual(to_visual(s, shape=False)) == s


def test_wrap_keeps_logical_line_order():
    out = to_visual('واحد اثنان ثلاثة أربعة خمسة', shape=False, wrap=12)
    assert [from_visual(l) for l in out.split(NL)] == ['واحد اثنان', 'ثلاثة أربعة', 'خمسة']


def test_wrap_never_splits_tokens():
    s = 'خذ __plural_for_parameter__1__{1=عنصر واحد|rest=عناصر}__ الآن'
    for line in wrap_logical(s, 5).split(NL):
        assert line.count('{') == line.count('}')


def test_involution_rate_on_official_arabic():
    vals = [v for p in GAME_DATA.glob('**/locale/ar/*.cfg') for v in read_cfg(p).values()]
    ok = sum(to_visual(from_visual(v), shape=False) == v for v in vals)
    assert ok / len(vals) >= 0.98  # measured 5768/5880 on 2.1.24; failures = known defects
