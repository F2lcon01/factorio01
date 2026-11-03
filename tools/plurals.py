"""Project plural rule: a block written as {1=singular|2=dual|rest=plural} becomes
{1=singular|2=dual|3=plural|…|10=plural|rest=singular} (Arabic: 3–10 take the plural, 11+ the singular).
python -E -m tools.plurals   (rewrites src/ar in place)"""
import re, sys
from tools.cfg import read_cfg, write_cfg
from tools.paths import MODULES, SRC, read_en

BLOCK = re.compile(r'(__plural_for_parameter__\d+__\{)([^}]*)(\}__)')


def _fix(m):
    forms = [f.partition('=') for f in m.group(2).split('|')]
    if [c for c, _, _ in forms] != ['1', '2', 'rest']:
        return m.group(0)
    one, two, many = (t for _, _, t in forms)
    body = '|'.join([f'1={one}', f'2={two}'] + [f'{n}={many}' for n in range(3, 11)] + [f'rest={one}'])
    return m.group(1) + body + m.group(3)


def normalize(text):
    return BLOCK.sub(_fix, text)


def main():
    changed = 0
    for m in MODULES:
        cur = read_cfg(SRC / f'{m}.cfg')
        new = {k: normalize(v) for k, v in cur.items()}
        changed += sum(new[k] != cur[k] for k in cur)
        write_cfg(SRC / f'{m}.cfg', new, list(read_en(m)))
    return changed


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('plural blocks normalized in', main(), 'values')
