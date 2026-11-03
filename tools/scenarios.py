"""Task 12: scenario / campaign / tutorial texts cannot be overridden by a mod (reports/spike.md #3),
so their Arabic files are patched in place, with a full backup and a byte-exact restore.
python -E -m tools.scenarios import | build | apply | restore | status"""
import hashlib, json, shutil, sys, time
from pathlib import Path
from tools.build import visual_value
from tools.cfg import read_cfg, write_cfg
from tools.import_official import classify
from tools.lint import check_value
from tools.paths import DIST, GAME_DATA, ROOT, WORK

SRC_SC = ROOT / 'src' / 'scenarios'
OUT_SC = DIST / 'scenarios'
BACKUPS = ROOT / 'backups'
TODO = WORK / 'scenarios-todo.jsonl'


def _sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


def en_files():
    """(relative 'base/.../locale/<file>.cfg', en path, game ar path) for every scenario-like locale file."""
    for loc in sorted(GAME_DATA.glob('base/**/locale')):
        rel = loc.relative_to(GAME_DATA)
        if len(rel.parts) > 1 and rel.parts[1] in ('scenarios', 'campaigns', 'tutorials'):
            for en in sorted((loc / 'en').glob('*.cfg')):
                yield (rel / en.name).as_posix(), en, loc / 'ar' / en.name


def import_():
    todo = []
    for rel, en_path, ar_path in en_files():
        en = read_cfg(en_path)
        official = read_cfg(ar_path) if ar_path.exists() else {}
        good = {}
        for k, e in en.items():
            if k not in official:
                todo.append({'file': rel, 'key': k, 'en': e, 'hint': '', 'reason': 'missing'})
                continue
            logical, reason = classify(e, official[k])
            if reason:
                todo.append({'file': rel, 'key': k, 'en': e, 'hint': logical, 'reason': reason})
            else:
                good[k] = logical
        write_cfg(SRC_SC / rel, good, list(en))
    TODO.parent.mkdir(parents=True, exist_ok=True)
    TODO.write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in todo) + '\n', encoding='utf-8', newline='\n')
    return todo


def add_translations(rows):
    """rows: [{'file', 'key', 'ar'}] → validated into src/scenarios; returns rejected rows."""
    en_of = {rel: en for rel, en, _ in en_files()}
    rejected, by_file = [], {}
    for r in rows:
        en = read_cfg(en_of[r['file']])
        errs = check_value(en[r['key']], r['ar'])
        if errs:
            rejected.append({**r, 'errors': errs})
        else:
            by_file.setdefault(r['file'], {})[r['key']] = r['ar']
    for rel, vals in by_file.items():
        cur = read_cfg(SRC_SC / rel)
        cur.update(vals)
        write_cfg(SRC_SC / rel, cur, list(read_cfg(en_of[rel])))
    return rejected


def build():
    for rel, en_path, _ in en_files():
        src = read_cfg(SRC_SC / rel)
        missing = set(read_cfg(en_path)) - set(src)
        if missing:
            raise SystemExit(f'{rel}: {len(missing)} keys untranslated, e.g. {sorted(missing)[:3]}')
        write_cfg(OUT_SC / rel, {k: visual_value(k, v) for k, v in src.items()}, list(read_cfg(en_path)))


def apply():
    stamp = time.strftime('%Y%m%d-%H%M%S')
    manifest = {}
    for rel, _, ar_path in en_files():
        built = OUT_SC / rel
        backup = BACKUPS / stamp / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        if ar_path.exists():
            shutil.copy2(ar_path, backup)
        manifest[rel] = {'original': _sha(ar_path) if ar_path.exists() else None, 'patched': _sha(built)}
    (BACKUPS / stamp / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    for rel, _, ar_path in en_files():  # write only after every backup succeeded
        ar_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT_SC / rel, ar_path)
    return stamp


def _latest_backup():
    stamps = sorted(p for p in BACKUPS.iterdir() if (p / 'manifest.json').exists()) if BACKUPS.exists() else []
    if not stamps:
        raise SystemExit('no backup found')
    return stamps[-1]


def restore():
    root = _latest_backup()
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    for rel, _, ar_path in en_files():
        if manifest[rel]['original'] is None:
            ar_path.unlink(missing_ok=True)  # file did not exist before the patch: our own file
        else:
            shutil.copy2(root / rel, ar_path)
            assert _sha(ar_path) == manifest[rel]['original'], rel
    return root.name


def status():
    manifest = json.loads((_latest_backup() / 'manifest.json').read_text(encoding='utf-8'))
    out = {'patched': 0, 'original': 0, 'other': 0}
    for rel, _, ar_path in en_files():
        h = _sha(ar_path) if ar_path.exists() else None
        out['patched' if h == manifest[rel]['patched'] else 'original' if h == manifest[rel]['original'] else 'other'] += 1
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1]
    if cmd == 'import':
        print('todo =', len(import_()))
    elif cmd == 'merge':  # work/scenarios-out.jsonl (or a given fix file) from the translator
        path = Path(sys.argv[2]) if len(sys.argv) > 2 else WORK / 'scenarios-out.jsonl'
        rows = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
        rej = add_translations(rows)
        print(f'merged={len(rows) - len(rej)} rejected={len(rej)}')
        for r in rej:
            print('  REJECTED', r['file'], r['key'], r['errors'])
        sys.exit(1 if rej else 0)
    else:
        print({'build': build, 'apply': apply, 'restore': restore, 'status': status}[cmd]())
