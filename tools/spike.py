"""Phase 0 gate: render test strings in the real game and screenshot them.
python -E -m tools.spike"""
import sys
from tools.harness import run
from tools.metrics import line_px
from tools.textfx import to_visual

WORDS = ('صفيحة حديد تصهر في الفرن الحجري ثم تستخدم في صناعة التروس والأنابيب والدوائر الإلكترونية '
         'وتحتاج إلى الفحم أو الخشب كوقود للأفران في بداية اللعبة').split()
TOOLTIP_PX = 356  # data/core/prototypes/style.lua:959-965 tooltip_label maximal_width


def line_of(target_px):
    """Shortest prefix of WORDS (cycled) whose rendered width reaches target_px."""
    out, i = [], 0
    while line_px(' '.join(out)) < target_px:
        out.append(WORDS[i % len(WORDS)])
        i += 1
    return ' '.join(out)


def build():
    widths = [250, 300, 330, 350, 370, 400]
    long_text = ' '.join(WORDS * 2)
    cfg = [
        'msg-intro=' + to_visual('نص اختبار لرسالة بداية اللعب الحر'),
        '[gui-menu]', 'single-player-menu=' + to_visual('لعب فردي'),
        '[item-name]', 'iron-plate=' + to_visual('صفيحة حديد'),
        '[fa-test]',
        'harakat=' + to_visual('العَرَبِيَّة لا إله إلا الله'),
        'tokens=' + to_visual('اضغط __CONTROL__build__ لوضع [item=iron-plate] على الحزام (الأحمر).'),
        'numbers=' + to_visual('أنتج 1.5 ألف دارة في الدقيقة بنسبة 20٪ أسرع.'),
        'prewrapped=' + to_visual(long_text, wrap=340, measure=line_px),
        'engine-wrapped=' + to_visual(long_text),
    ]
    rows = []
    for w in widths:
        cfg.append(f'w{w}=' + to_visual(line_of(w)))
        rows += [f'--- {w}px (measured {line_px(line_of(w)):.0f})', ['fa-test.w%d' % w]]
    shots = [
        {'name': 'basics', 'title': 'FA basics', 'rows': [
            ['gui-menu.single-player-menu'], ['item-name.iron-plate'], ['item-name.copper-plate'],
            ['msg-intro'], ['fa-test.harakat'], ['fa-test.tokens'], ['fa-test.numbers']]},
        {'name': 'wrap', 'title': 'FA wrap 356px', 'rows': rows},
        {'name': 'paragraph', 'title': 'FA paragraph', 'rows': [
            '--- prewrapped @340px', ['fa-test.prewrapped'], '--- engine-wrapped', ['fa-test.engine-wrapped']]},
        {'name': 'production', 'gui_type': 'production'},
    ]
    return shots, '\n'.join(cfg) + '\n'


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    shots, cfg = build()
    for p in run(shots, cfg, tag='phase0'):
        print(p)
