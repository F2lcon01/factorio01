"""Apply reviewed manual decisions to src/ar, after import/glossary/terms/merge so a re-import never loses them:
1. term_migrations.json [[old, new], ...] — a renamed term, replaced in every value (main + scenarios)
2. corrections.json {"module:section/key": "arabic"} — single reviewed values
3. tools.plurals — project plural rule
python -E -m tools.corrections"""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import check_value
from tools.paths import MODULES, ROOT, SRC, read_en
from tools.plurals import normalize


def migrate(text, pairs):
    for old, new in pairs:  # longest first in the file, so a phrase is replaced before its prefix
        text = text.replace(old, new)
    return text


def apply():
    pairs = json.loads((ROOT / 'term_migrations.json').read_text(encoding='utf-8'))
    fixes = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    by_module = {}
    for full, ar in fixes.items():
        m, k = full.split(':', 1)
        errs = check_value(read_en(m)[k], ar)
        if errs:
            raise SystemExit(f'{full}: {errs}')
        by_module.setdefault(m, {})[k] = ar
    migrated = 0
    for m in MODULES:
        cur = read_cfg(SRC / f'{m}.cfg')
        cur.update(by_module.get(m, {}))
        new = {k: normalize(migrate(v, pairs)) for k, v in cur.items()}
        migrated += sum(new[k] != cur[k] for k in cur)
        write_cfg(SRC / f'{m}.cfg', new, list(read_en(m)))
    for p in (ROOT / 'src' / 'scenarios').rglob('*.cfg'):
        cur = read_cfg(p)
        new = {k: normalize(migrate(v, pairs)) for k, v in cur.items()}
        if new != cur:
            migrated += sum(new[k] != cur[k] for k in cur)
            write_cfg(p, new, list(cur))
    return len(fixes), migrated


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('corrections=%d migrated/normalized values=%d' % apply())
