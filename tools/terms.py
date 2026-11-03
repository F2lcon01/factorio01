"""Translate prototype names once (consistency), before the description batches.
python -E -m tools.terms extract | check | apply"""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.paths import SRC, WORK, read_en
from tools.textfx import ARABIC_RE

PROTO_NAME_SECTIONS = {
    'item-name', 'entity-name', 'technology-name', 'recipe-name', 'fluid-name', 'tile-name', 'equipment-name',
    'space-location-name', 'quality-name', 'asteroid-chunk-name', 'surface-name', 'autoplace-control-names',
    'map-gen-preset-name', 'decorative-name', 'ammo-category-name', 'airborne-pollutant-name', 'fuel-category-name'}
TERMS = WORK / 'terms'


def _todo():
    return [json.loads(l) for l in (WORK / 'todo.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]


def _is_term(row):
    return row['key'].split('/', 1)[0] in PROTO_NAME_SECTIONS and '__' not in row['en']


def extract():
    terms = {}
    for r in _todo():
        if _is_term(r):
            t = terms.setdefault(r['en'].strip().lower(), {'en': r['en'].strip(), 'hint': r['hint'], 'keys': []})
            t['keys'].append(f"{r['module']}:{r['key']}")
    TERMS.mkdir(parents=True, exist_ok=True)
    rows = sorted(terms.values(), key=lambda t: t['en'].lower())
    (TERMS / 'terms.jsonl').write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in rows) + '\n',
                                       encoding='utf-8', newline='\n')
    print('terms =', len(rows))


def check():
    src = [json.loads(l) for l in (TERMS / 'terms.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    try:
        out = [json.loads(l) for l in (TERMS / 'terms.out.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    except (OSError, json.JSONDecodeError) as e:
        return [f'invalid JSON or missing file: {e}']
    errs = [] if len(out) == len(src) else [f'count {len(out)} != {len(src)}']
    for i, (s, o) in enumerate(zip(src, out), 1):
        if o.get('en') != s['en']:
            errs.append(f'line {i}: expected en "{s["en"]}", got "{o.get("en")}"')
        elif not ARABIC_RE.search(o.get('ar', '')) or any(0xFB50 <= ord(c) <= 0xFEFF for c in o.get('ar', '')):
            errs.append(f'line {i} "{s["en"]}": ar must be plain Arabic')
    return errs


def apply():
    errs = check()
    if errs:
        sys.exit('\n'.join(errs[:20]))
    ar_of = {json.loads(l)['en'].lower(): json.loads(l)['ar']
             for l in (TERMS / 'terms.out.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
    rest, by_module = [], {}
    for r in _todo():
        if _is_term(r) and r['en'].strip().lower() in ar_of:
            by_module.setdefault(r['module'], {})[r['key']] = ar_of[r['en'].strip().lower()]
        else:
            rest.append(r)
    for m, vals in by_module.items():
        cur = read_cfg(SRC / f'{m}.cfg')
        cur.update(vals)
        write_cfg(SRC / f'{m}.cfg', cur, list(read_en(m)))
    (WORK / 'todo.jsonl').write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in rest) + '\n',
                                     encoding='utf-8', newline='\n')
    print('name keys filled =', sum(len(v) for v in by_module.values()), '| todo left =', len(rest))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1]
    if cmd == 'check':
        e = check()
        print('\n'.join(e[:40]) + f'\nerrors={len(e)}')
        sys.exit(1 if e else 0)
    {'extract': extract, 'apply': apply}[cmd]()
