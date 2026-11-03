"""Apply reviewed manual decisions to src/ar, after import/glossary/terms/merge so a re-import never loses them:
1. term_migrations.json [[old, new], ...] — a renamed term, replaced in every value (main + scenarios)
2. corrections.json {"module:section/key": "arabic"} — single reviewed values
3. tools.plurals — project plural rule; Western digits (٠-٩ / ۰-۹ → 0-9)
4. programmable-speaker-note C4/C#4… → solfège (دو4 / دو#4…), the Arabic music convention
python -E -m tools.corrections"""
import json, re, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import check_value
from tools.paths import MODULES, ROOT, SRC, read_en
from tools.plurals import normalize as normalize_plurals

DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
SOLFEGE = {'C': 'دو', 'D': 'ري', 'E': 'مي', 'F': 'فا', 'G': 'صول', 'A': 'لا', 'B': 'سي'}
NOTE_RE = re.compile(r'^([A-G])(#?)(\d)$')


def normalize(text):
    return normalize_plurals(text.translate(DIGITS))


def note_names(module):
    """programmable-speaker-note/C#4 = 'C#4' → 'دو#4'."""
    out = {}
    for k, e in read_en(module).items():
        m = NOTE_RE.match(e)
        if k.startswith('programmable-speaker-note/') and m:
            out[k] = SOLFEGE[m.group(1)] + m.group(2) + m.group(3)
    return out


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
        cur.update({k: v for k, v in note_names(m).items() if k in cur})
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
