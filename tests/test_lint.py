from tools.lint import check_value


def test_ok():
    assert check_value('Press __CONTROL__build__.', 'اضغط __CONTROL__build__.') == []


def test_token_changed():
    assert 'tokens' in check_value('Press __CONTROL__build__.', 'اضغط __CONTROL__بناء__.')


def test_newline_count_must_match():
    assert 'tokens' in check_value('a\\nb', 'أ ب')


def test_plural_without_condition():
    en = '__1__ __plural_for_parameter__1__{1=change|rest=changes}__'
    assert 'plural' in check_value(en, '__1__ __plural_for_parameter__1__{1=تغيير|تغييرات}__')


def test_presentation_forms_forbidden_in_source():
    assert 'forbidden-char' in check_value('Plate', 'ﺻﻔﻴﺤﺔ')


def test_untranslated_latin():
    assert 'no-arabic' in check_value('Iron plate', 'Iron plate')
    assert check_value('Iron plate', 'Iron plate', allow_latin=True) == []
