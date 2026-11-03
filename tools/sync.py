"""After a game update: list new/changed/removed English keys and append them to work/todo.jsonl.
--refresh-snapshot: run only after every queued key is merged; marks current English as translated."""
import hashlib, json, sys
from tools.cfg import read_cfg
from tools.paths import MODULES, ROOT, SRC, WORK, read_en


def refresh_snapshot():
    snap = {}
    for m in MODULES:
        src = read_cfg(SRC / f'{m}.cfg')
        for k, e in read_en(m).items():
            if k in src:
                snap[f'{m}:{k}'] = hashlib.sha1(e.encode('utf-8')).hexdigest()
    (ROOT / 'src' / 'en_snapshot.json').write_text(json.dumps(snap, indent=0), encoding='utf-8')
    print('snapshot keys =', len(snap))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    snap = json.loads((ROOT / 'src' / 'en_snapshot.json').read_text(encoding='utf-8'))
    todo, seen = [], set()
    for m in MODULES:
        for k, e in read_en(m).items():
            sk = f'{m}:{k}'; seen.add(sk)
            h = hashlib.sha1(e.encode('utf-8')).hexdigest()
            if sk not in snap:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'new'})
            elif snap[sk] != h:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'changed'})
    removed = sorted(set(snap) - seen)
    WORK.mkdir(exist_ok=True)
    with open(WORK / 'todo.jsonl', 'a', encoding='utf-8') as f:
        for t in todo:
            f.write(json.dumps(t, ensure_ascii=False) + '\n')
    print(f'new/changed={len(todo)} removed={len(removed)}')


if __name__ == '__main__':
    refresh_snapshot() if '--refresh-snapshot' in sys.argv else main()
