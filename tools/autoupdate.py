"""Content side of the smart update (called by tools/auto_update.ps1 when the game version changed, or with -Force).
1. compare every English string with src/en_snapshot.json
2. new strings: take the game's own Arabic when it is valid (the build shapes it); otherwise list them
3. changed English: keep our translation (better than English) and list it for review
4. rebuild the mod with version = game version and factorio_version = game major.minor
5. rebuild the scenario files, filling new keys the same way
Prints one JSON line for the caller and writes reports/auto-update.md.  python -E -m tools.autoupdate"""
import hashlib, json, sys, time
from tools import scenarios
from tools.build import build, game_version
from tools.bundle import add_tools
from tools.cfg import read_cfg, write_cfg
from tools.corrections import apply as apply_corrections
from tools.import_official import take_official
from tools.lint import _allow
from tools.paths import GAME_DATA, MODULES, REPORTS, ROOT, SRC, read_en

SNAP = ROOT / 'src' / 'en_snapshot.json'


def _sha(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def sync():
    snap = json.loads(SNAP.read_text(encoding='utf-8'))
    allow = _allow()
    res = {'new': 0, 'changed': 0, 'auto_official': 0, 'untranslated': [], 'review': []}
    for m in MODULES:
        en, src = read_en(m), read_cfg(SRC / f'{m}.cfg')
        official = read_cfg(GAME_DATA / m / 'locale' / 'ar' / f'{m}.cfg')
        touched = False
        for k, e in en.items():
            sk = f'{m}:{k}'
            if snap.get(sk) == _sha(e):
                continue
            if sk not in snap or k not in src:
                res['new'] += 1
                logical = take_official(e, official.get(k), allow_latin=sk in allow)
                if logical is None:
                    res['untranslated'].append(sk)  # stays out of the snapshot → reported again next time
                    continue
                src[k], snap[sk], touched = logical, _sha(e), True
                res['auto_official'] += 1
            else:
                res['changed'] += 1
                res['review'].append(sk)  # old hash kept → reported until reviewed (tools.sync --refresh-snapshot)
        if touched:
            write_cfg(SRC / f'{m}.cfg', src, list(en))
    SNAP.write_text(json.dumps(snap, indent=0), encoding='utf-8', newline='\n')
    return res


def report(version, res):
    REPORTS.mkdir(exist_ok=True)
    lines = [f'# Auto-update — {time.strftime("%Y-%m-%d %H:%M")} — Factorio {version}', '',
             f'- new strings: {res["new"]} (taken from the game\'s Arabic: {res["auto_official"]})',
             f'- still untranslated (shown in English): {len(res["untranslated"])}',
             f'- English changed, translation kept (review): {len(res["review"])}', '']
    for title, keys in (('Untranslated', res['untranslated']), ('Review', res['review'])):
        if keys:
            lines += [f'## {title}', ''] + [f'- `{k}`' for k in keys[:300]] + ['']
    (REPORTS / 'auto-update.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    version = game_version()
    res = sync()
    apply_corrections()        # decisions, term migrations, plural rule, digits also apply to newly taken text
    mod = build(version)
    add_tools(mod)             # language tool + scenario patch inside the mod (also builds the scenario files)
    report(version, res)
    print(json.dumps({'game_version': version, 'mod': mod.name, 'new': res['new'],
                      'auto_official': res['auto_official'], 'untranslated': len(res['untranslated']),
                      'review': len(res['review'])}))


if __name__ == '__main__':
    main()
