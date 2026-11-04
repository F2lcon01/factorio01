"""Gallery images for the mod portal page → docs/portal/<n>-<name>.png (uploaded by tools/portal_page.ps1).
1: official Arabic vs this mod, drawn the way the engine draws: the game's own font, glyph by glyph, left to right,
   no shaping (Pillow without libraqm does exactly that; checked at runtime). Strings come from the game's own file
   and from the built mod, not retyped.
2-4: crops of real in-game screenshots (reports/screens, made by tools.visual_check / tools.scenario_check).
5: the language tool window (docs/images/tool-states.png).
6: the mods translator window (docs/images/translator-busy.png, made with Translate-Mods.ps1 -Snapshot -PreviewBusy).
python -E -m tools.portal_images <version>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features
from tools.cfg import read_cfg
from tools.paths import DIST, GAME_DATA, MODULES, REPORTS, ROOT, read_en
from tools.textfx import ARABIC_RE, to_visual

OUT = ROOT / 'docs' / 'portal'
ROWS = ['item-name/iron-plate', 'entity-name/assembling-machine-2', 'technology-name/advanced-circuit',
        'entity-name/bulk-inserter', 'entity-name/foundry', 'space-location-name/vulcanus',
        'tips-and-tricks-item-name/fast-replace']
BG, PANEL, TEXT, ORANGE = (36, 36, 36), (49, 48, 49), (255, 230, 192), (255, 156, 0)
BAD, GOOD, GREY = (229, 115, 115), (129, 199, 132), (170, 170, 170)


def _font(name, size):
    return ImageFont.truetype(str(GAME_DATA / 'core' / 'fonts' / name), size)


def _merged(base):
    out = {}
    for m in MODULES:
        out.update(read_cfg(base(m)))
    return out


def before_after(version, path):
    if features.check('raqm'):
        sys.exit('Pillow has libraqm: it would shape the text and hide what the engine really shows')
    official = _merged(lambda m: GAME_DATA / m / 'locale' / 'ar' / f'{m}.cfg')
    ours = _merged(lambda m: DIST / f'arabic-complete_{version}' / 'locale' / 'ar' / f'{m}.cfg')
    en = {}
    for m in MODULES:
        en.update(read_en(m))
    ar, ar_bold, latin = _font('NotoSansArabic-Regular.ttf', 30), _font('NotoSansArabic-Bold.ttf', 30), \
        _font('TitilliumWeb-Regular.ttf', 24)
    cols, row_h, top = (40, 400, 820), 62, 150
    img = Image.new('RGB', (1240, top + row_h * len(ROWS) + 90), BG)
    d = ImageDraw.Draw(img)
    d.text((620, 40), to_visual('العربية في اللعبة: قبل المود وبعده'), font=ar_bold, fill=ORANGE, anchor='mm')
    for x, label, color in ((cols[0], 'English', GREY), (cols[1], to_visual('الترجمة الحالية في اللعبة'), BAD),
                            (cols[2], to_visual('مع هذا المود'), GOOD)):
        d.text((x, 105), label, font=ar_bold if label != 'English' else latin, fill=color, anchor='lm')
    for i, k in enumerate(ROWS):
        y = top + i * row_h
        d.rectangle([20, y, 1220, y + row_h - 8], fill=PANEL)
        cy = y + (row_h - 8) // 2
        d.text((cols[0], cy), en[k], font=latin, fill=GREY, anchor='lm')
        o = official.get(k) or en[k]   # missing → the game falls back to English
        d.text((cols[1], cy), o, font=ar if ARABIC_RE.search(o) else latin, fill=TEXT, anchor='lm')
        d.text((cols[2], cy), ours[k], font=ar, fill=TEXT, anchor='lm')
    note = to_visual('رُسمت بخط اللعبة نفسه وبطريقة المحرك: حرفاً حرفاً بلا تشكيل، والنصوص من ملفات اللعبة والمود')
    d.text((620, img.height - 45), note, font=_font('NotoSansArabic-Regular.ttf', 22), fill=GREY, anchor='mm')
    img.save(path, optimize=True)


def crop(src, box, scale, path):
    im = Image.open(src).convert('RGB').crop(box)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    im.save(path, optimize=True)


def main(version):
    OUT.mkdir(parents=True, exist_ok=True)
    screens = REPORTS / 'screens'
    before_after(version, OUT / '1-before-after.png')
    crop(screens / 'phase3-1.0.0-achievement.png', (796, 18, 1124, 548), 2, OUT / '2-achievements.png')
    crop(screens / 'phase4-scenario-zoom.png', (0, 56, 520, 196), 2, OUT / '3-freeplay-intro.png')   # below the
    crop(ROOT / 'docs' / 'images' / 'in-game-tooltip.png', (0, 60, 536, 480), 1, OUT / '4-long-description.png')  # test caption
    crop(ROOT / 'docs' / 'images' / 'tool-states.png', (0, 0, 968, 399), 1, OUT / '5-language-tool.png')
    crop(ROOT / 'docs' / 'images' / 'translator-busy.png', (0, 0, 836, 689), 1, OUT / '6-mods-translator.png')
    for p in sorted(OUT.glob('*.png')):
        print(p.name, Image.open(p).size, p.stat().st_size)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1])
