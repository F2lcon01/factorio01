"""Validate src/ar against the game's English locale."""
import collections, hashlib, json, re, sys
from tools.cfg import read_cfg
from tools.paths import MODULES, ROOT, SRC, read_en

TOKEN_RE = re.compile(r'__[A-Z][A-Z_]*__(?:\d+__)?(?:[a-z0-9][a-z0-9\-]*__)?|__\d+__'
                      r'|\[/?[a-z\-]+(?:=[^\]]*)?\]|\\n')
PLURAL_RE = re.compile(r'__plural_for_parameter__(\d+)__\{([^}]*)\}__')
COND_RE = re.compile(r'^(?:\d+|rest|ends in \d+)$')
ARABIC_RE = re.compile(r'[\u0621-\u064A]')
LATIN_RE = re.compile(r'[A-Za-z]{2,}')
FORBIDDEN_RE = re.compile(r'[\uFB50-\uFDFF\uFE70-\uFEFF\uE000-\uF8FF\u200E\u200F\u202A-\u202E\u2066-\u2069]')


TOOLTIP_TEXT = re.compile(r'\[tooltip=[^,\]]*,')  # visible text of [tooltip=text,key] is translatable


def signature(s):
    s = TOOLTIP_TEXT.sub('[tooltip=*,', s)
    plurals = [f'P{n}' for n, _ in PLURAL_RE.findall(s)]
    return collections.Counter(TOKEN_RE.findall(PLURAL_RE.sub('', s)) + plurals)


def check_value(en, ar, allow_latin=False):
    errs = []
    if signature(en) != signature(ar):
        errs.append('tokens')
    for _, body in PLURAL_RE.findall(ar):
        if any('=' not in f or not COND_RE.match(f.partition('=')[0]) for f in body.split('|')):
            errs.append('plural')
            break
    if FORBIDDEN_RE.search(ar):
        errs.append('forbidden-char')
    if not allow_latin and LATIN_RE.search(TOKEN_RE.sub('', en)) and not ARABIC_RE.search(ar):
        errs.append('no-arabic')
    return errs


def _allow():
    p = ROOT / 'lint_allow.txt'
    return set(p.read_text(encoding='utf-8').split()) if p.exists() else set()


def lint_module(module):
    en, allow = read_en(module), _allow()
    src_path = SRC / f'{module}.cfg'
    ar = read_cfg(src_path) if src_path.exists() else {}
    snap_path = ROOT / 'src' / 'en_snapshot.json'
    snap = json.loads(snap_path.read_text(encoding='utf-8')) if snap_path.exists() else {}
    errors, warnings = [], []
    for k, e in en.items():
        if k not in ar:
            errors.append(f'{module}:{k}: missing')
            continue
        for err in check_value(e, ar[k], allow_latin=f'{module}:{k}' in allow):
            errors.append(f'{module}:{k}: {err}')
        h = hashlib.sha1(e.encode('utf-8')).hexdigest()
        if snap.get(f'{module}:{k}', h) != h:
            warnings.append(f'{module}:{k}: stale (English changed)')
    for k in ar.keys() - en.keys():
        warnings.append(f'{module}:{k}: obsolete')
    return errors, warnings


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    total_e = total_w = 0
    for m in MODULES:
        e, w = lint_module(m)
        total_e += len(e); total_w += len(w)
        print(f'{m:15} errors={len(e):5} warnings={len(w):5}')
        for line in (e + w)[:20]:
            print('   ', line)
    sys.exit(1 if total_e else 0)
