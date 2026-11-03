"""Apply reviewed manual corrections (corrections.json {"module:section/key": "arabic"}) to src/ar.
Runs after import/glossary/terms/merge so a re-import never loses them. python -E -m tools.corrections"""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import check_value
from tools.paths import ROOT, SRC, read_en


def apply():
    fixes = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    by_module = {}
    for full, ar in fixes.items():
        m, k = full.split(':', 1)
        errs = check_value(read_en(m)[k], ar)
        if errs:
            raise SystemExit(f'{full}: {errs}')
        by_module.setdefault(m, {})[k] = ar
    for m, vals in by_module.items():
        cur = read_cfg(SRC / f'{m}.cfg')
        cur.update(vals)
        write_cfg(SRC / f'{m}.cfg', cur, list(read_en(m)))
    return len(fixes)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('corrections applied =', apply())
