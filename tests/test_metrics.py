from tools.metrics import line_px
from tools.textfx import NL, from_visual, to_visual, wrap_logical


def test_narrow_letters_are_narrower_than_wide_ones():
    assert line_px('اااا') < line_px('سسسس')


def test_width_is_additive_for_spaced_words():
    assert abs(line_px('حديد حديد') - (2 * line_px('حديد') + line_px(' '))) < 0.01


def test_icon_token_counts_as_fixed_width():
    assert line_px('[item=iron-plate]') == line_px('[item=copper-plate]') > 0


def test_pixel_wrap_keeps_every_line_within_limit():
    text = ' '.join(['صفيحة حديد مصهورة في الفرن الحجري'] * 6)
    out = to_visual(text, shape=False, wrap=200, measure=line_px)
    for line in out.split(NL):
        assert line_px(from_visual(line)) <= 200
