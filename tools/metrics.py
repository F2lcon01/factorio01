"""Pixel width of a logical Arabic line as Factorio renders it with the 'default' font (14px).
Glyphs come from the game's own font files in the same fallback order as core/locale/en/info.json."""
from functools import lru_cache
from fontTools.ttLib import TTFont
from tools.paths import GAME_DATA
from tools.textfx import FORMAT_RE, HARAKAT_RE, INLINE_RE, _RESHAPER

SIZE = 14  # data/core/prototypes/fonts.lua: name = "default", size = 14
CHAIN = ['TitilliumWeb-Regular', 'Lilittium-Regular', 'NotoSans-Regular', 'NotoSansCJKtc-Regular',
         'NotoSansThai-Regular', 'NotoSansArabic-Regular', 'NotoSansHebrew-Regular', 'DejaVuSans']
# Runtime-resolved tokens have no fixed text; these are conservative estimates.
TOKEN_PX = {'icon': 18, 'param': 40, 'plural': 50, 'control': 90}


@lru_cache(maxsize=None)
def _font(name):
    f = TTFont(GAME_DATA / 'core' / 'fonts' / f'{name}.ttf', lazy=True)
    return f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm


@lru_cache(maxsize=None)
def char_px(c):
    for name in CHAIN:
        cmap, hmtx, upem = _font(name)
        glyph = cmap.get(ord(c))
        if glyph is not None:
            return hmtx[glyph][0] * SIZE / upem
    return SIZE  # missing glyph renders as a box


def _token_px(tok):
    if tok.startswith('['):
        return TOKEN_PX['icon']
    if tok.startswith('__plural'):
        return TOKEN_PX['plural']
    if tok[2:3].isdigit():
        return TOKEN_PX['param']
    return TOKEN_PX['control']


def _shaped_px(s):
    return sum(char_px(c) for c in _RESHAPER.reshape(HARAKAT_RE.sub('', s)))


def line_px(logical):
    text, px, pos = FORMAT_RE.sub('', logical), 0.0, 0
    for m in INLINE_RE.finditer(text):
        px += _shaped_px(text[pos:m.start()]) + _token_px(m.group(0))
        pos = m.end()
    return px + _shaped_px(text[pos:])
