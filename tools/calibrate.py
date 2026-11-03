"""Find the measured width (tools.metrics.line_px) at which the engine starts wrapping inside a
356px tooltip_label. python -E -m tools.calibrate"""
import sys
from tools.harness import run
from tools.metrics import line_px
from tools.spike import WORDS
from tools.textfx import to_visual


def exact_line(target_px):
    """Longest prefix of WORDS (cycled) whose measured width stays <= target_px."""
    out, i = [], 0
    while line_px(' '.join(out + [WORDS[i % len(WORDS)]])) <= target_px:
        out.append(WORDS[i % len(WORDS)])
        i += 1
    return ' '.join(out)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cfg, rows = ['[fa-test]'], []
    for t in range(440, 541, 10):
        line = exact_line(t)
        cfg.append(f'c{t}=' + to_visual(line))
        rows += [f'--- {line_px(line):.0f}', [f'fa-test.c{t}']]
    for p in run([{'name': 'calibrate', 'title': 'FA calibrate', 'rows': rows}], '\n'.join(cfg) + '\n', tag='phase0'):
        print(p)
