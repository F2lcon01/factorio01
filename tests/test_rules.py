from tools.lint import check_value
from tools.plurals import normalize
from tools.textfx import from_visual, to_visual


def test_plural_with_only_1_2_rest_gets_arabic_agreement():
    s = 'منذ __1__ __plural_for_parameter__1__{1=يوم|2=يومين|rest=أيام}__'
    out = normalize(s)
    assert '|3=أيام|' in out and '|10=أيام|' in out and out.endswith('|rest=يوم}__')


def test_plural_already_following_rule_or_other_shapes_untouched():
    done = '__plural_for_parameter__1__{1=a|2=b|3=c|4=c|5=c|6=c|7=c|8=c|9=c|10=c|rest=a}__'
    assert normalize(done) == done
    other = '__plural_for_parameter__1__{1=عنصر|rest=عناصر}__'
    assert normalize(other) == other


def test_eastern_digits_become_western():
    from tools.corrections import normalize as fix
    assert fix('وحدة الجودة ٣ و عشب ۲') == 'وحدة الجودة 3 و عشب 2'


def test_plural_phrases_with_parameters_are_left_alone():
    s = '__plural_for_parameter__1__{1=المحطة معطلة|2=المحطتان معطلتان|rest=كل المحطات الـ __1__ معطلة}__.'
    assert normalize(s) == s


def test_tooltip_tag_visible_text_may_be_translated_but_key_must_stay():
    en = 'See [tooltip=Provider chests,tips-and-tricks-item-description.storage-chest-list].'
    assert check_value(en, 'انظر [tooltip=صناديق المزود,tips-and-tricks-item-description.storage-chest-list].') == []
    assert 'tokens' in check_value(en, 'انظر [tooltip=صناديق المزود,other-key].')


def test_comparison_signs_are_mirrored_so_meaning_survives_reversal():
    out = to_visual('أ ≤ ب', shape=False)
    assert out == 'ب ≥ أ'  # read right-to-left: «أ ≤ ب»
    assert from_visual(out) == 'أ ≤ ب'


def test_tooltip_tag_text_is_reversed_with_the_line():
    s = 'انظر [tooltip=صناديق المزود,a.b-c].'
    out = to_visual(s, shape=False)
    assert '[tooltip=دوزملا قيدانص,a.b-c]' in out
    assert from_visual(out) == s
