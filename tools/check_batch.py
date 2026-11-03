"""Validate work/out/NNN.jsonl against work/batches/NNN.jsonl. Read-only: safe to run in parallel.
python -E -m tools.check_batch NNN   (exit 1 on errors; glossary hints are warnings)"""
import json, re, sys
from tools.lint import _allow, check_value
from tools.paths import WORK


def _rows(path):
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]


def check(n):
    src = _rows(WORK / 'batches' / f'{n}.jsonl')
    try:
        out = _rows(WORK / 'out' / f'{n}.jsonl')
    except (OSError, json.JSONDecodeError) as e:
        return [f'invalid JSON or missing file: {e}'], []
    gl = json.loads((WORK / 'batches' / f'{n}.glossary.json').read_text(encoding='utf-8'))
    allow, errs, warns = _allow(), [], []
    if len(out) != len(src):
        errs.append(f'count {len(out)} != {len(src)}')
    for i, (s, o) in enumerate(zip(src, out), 1):
        if (o.get('module'), o.get('key')) != (s['module'], s['key']):
            errs.append(f'line {i}: expected {s["module"]}:{s["key"]}, got {o.get("module")}:{o.get("key")}')
            continue
        ar = o.get('ar', '')
        for e in check_value(s['en'], ar, allow_latin=f'{s["module"]}:{s["key"]}' in allow):
            errs.append(f'line {i} {s["key"]}: {e}')
        for term, want in gl.items():
            if re.search(rf'\b{re.escape(term)}\b', s['en'].lower()) and want not in ar:
                warns.append(f'line {i} {s["key"]}: glossary "{term}" -> "{want}" not found')
    return errs, warns


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    errs, warns = check(sys.argv[1])
    for e in errs:
        print('ERROR', e)
    for w in warns[:40]:
        print('WARN ', w)
    print(f'errors={len(errs)} warnings={len(warns)}')
    sys.exit(1 if errs else 0)
