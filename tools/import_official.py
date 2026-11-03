"""Official visual ar -> logical src; everything defective or missing goes to todo."""
import hashlib, json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import _allow, check_value
from tools.paths import GAME_DATA, MODULES, REPORTS, ROOT, SRC, WORK, read_en
from tools.textfx import from_visual, to_visual


def classify(en, vis, allow_latin=False):
    logical = from_visual(vis)
    if to_visual(logical, shape=False) != vis:
        return logical, 'not-involutive'
    if en.rstrip().endswith('.') and vis.rstrip().endswith('.') and not vis.lstrip().startswith('.'):
        return logical, 'direction'
    errs = check_value(en, logical, allow_latin=allow_latin)
    return logical, (errs[0] if errs else None)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    todo, snap, counts, allow = [], {}, {}, _allow()
    for m in MODULES:
        en = read_en(m)
        official = read_cfg(GAME_DATA / m / 'locale' / 'ar' / f'{m}.cfg')
        good = {}
        for k, e in en.items():
            snap[f'{m}:{k}'] = hashlib.sha1(e.encode('utf-8')).hexdigest()
            if k not in official:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'missing'})
                continue
            logical, reason = classify(e, official[k], allow_latin=f'{m}:{k}' in allow)
            if reason:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': logical, 'reason': reason})
            else:
                good[k] = logical
        write_cfg(SRC / f'{m}.cfg', good, list(en))
    for t in todo:
        counts[t['reason']] = counts.get(t['reason'], 0) + 1
    WORK.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
    (WORK / 'todo.jsonl').write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in todo) + '\n', encoding='utf-8')
    (ROOT / 'src' / 'en_snapshot.json').write_text(json.dumps(snap, indent=0), encoding='utf-8')
    rows = '\n'.join(f'| {r} | {n} |' for r, n in sorted(counts.items(), key=lambda x: -x[1]))
    (REPORTS / 'defects.md').write_text(f'| reason | keys |\n|---|---|\n{rows}\n', encoding='utf-8')
    print(counts, 'todo total =', len(todo))


if __name__ == '__main__':
    main()
