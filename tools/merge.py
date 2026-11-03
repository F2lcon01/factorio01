"""Validate translated batch output and merge it into src/ar/<module>.cfg."""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import _allow, check_value
from tools.paths import SRC, WORK, read_en


def merge(n: str):
    rows = [json.loads(l) for l in (WORK / 'out' / f'{n}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    rejected, by_module, allow = [], {}, _allow()  # same allowlist as tools.check_batch and tools.lint
    for r in rows:
        errs = check_value(read_en(r['module'])[r['key']], r['ar'], allow_latin=f"{r['module']}:{r['key']}" in allow)
        if errs:
            rejected.append({**r, 'errors': errs})
        else:
            by_module.setdefault(r['module'], {})[r['key']] = r['ar']
    for m, vals in by_module.items():
        cur = read_cfg(SRC / f'{m}.cfg')
        cur.update(vals)
        write_cfg(SRC / f'{m}.cfg', cur, list(read_en(m)))
    (WORK / 'out' / f'{n}.rejected.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in rejected) + '\n', encoding='utf-8')
    return len(rows) - len(rejected), len(rejected)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('merged=%d rejected=%d' % merge(sys.argv[1]))
