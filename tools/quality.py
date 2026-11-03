"""Heuristic quality scan of the logical source (main + scenarios): reports/quality.md.
reversed-line : a line starting with sentence-final punctuation → stored in the wrong direction
latin-leftover: lowercase English word outside tokens → untranslated fragment
python -E -m tools.quality"""
import re, sys
from tools.cfg import read_cfg
from tools.paths import GAME_DATA, MODULES, REPORTS, ROOT, SRC, read_en
from tools.textfx import FORMAT_RE, INLINE_RE, NL

LEAD_PUNCT = re.compile(r'^[.،؛:!؟)]')
LATIN_WORD = re.compile(r'\b[a-z]{3,}\b')


def scan_value(en, ar):
    issues = []
    for line in ar.split(NL):
        bare = FORMAT_RE.sub('', line).strip()  # tokens stay: '__1__: اختر' is correct, not reversed
        if len(bare) > 1 and LEAD_PUNCT.match(bare):
            issues.append('reversed-line')
            break
    en_words = set(LATIN_WORD.findall(INLINE_RE.sub('', en).lower()))
    left = set(LATIN_WORD.findall(INLINE_RE.sub('', FORMAT_RE.sub('', ar)))) & en_words
    if left:
        issues.append('latin-leftover:' + ','.join(sorted(left)))
    return issues


def sources():
    for m in MODULES:
        yield m, read_en(m), read_cfg(SRC / f'{m}.cfg')
    sc = ROOT / 'src' / 'scenarios'
    for p in sorted(sc.rglob('*.cfg')):
        rel = p.relative_to(sc)  # base/<kind>/<name>/locale/<file>.cfg
        yield rel.as_posix(), read_cfg(GAME_DATA / rel.parent / 'en' / rel.name), read_cfg(p)


def main():
    rows = []
    for src, en, ar in sources():
        for k, v in ar.items():
            for issue in scan_value(en.get(k, ''), v):
                rows.append((src, k, issue, v[:90]))
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'quality.md').write_text(
        '| source | key | issue | text |\n|---|---|---|---|\n' +
        '\n'.join(f'| {s} | `{k}` | {i} | {t} |' for s, k, i, t in rows) + '\n', encoding='utf-8', newline='\n')
    print('issues =', len(rows))
    return rows


# English that legitimately stays Latin inside Arabic text (brands, URLs, chat commands, Steam branch names)
LEGIT_LATIN = {'com', 'factorio', 'help', 'command', 'online', 'mode', 'experimental', 'latest', 'editor', 'zip'}
# Existing texts that use a term changed by a glossary decision (cliff = جرف/أجراف)
TERM_REVIEW = ['base:map-gen-preset-description/lakes', 'core:gui-map-generator/cliff-frequency-description',
               'core:gui-map-generator/cliff-continuity-description', 'core:gui-map-editor/cliffs',
               'core:gui-map-editor-title/cliff-editor', 'core:gui-map-editor-instructions/build-cliffs',
               'core:gui-map-editor-instructions/remove-cliffs']


def requeue():
    """Append real main-module issues to work/todo.jsonl (reason 'review', hint = current text)."""
    import json
    from tools.paths import WORK
    todo_path = WORK / 'todo.jsonl'
    queued = {(r['module'], r['key']) for r in map(json.loads, filter(str.strip, todo_path.read_text(encoding='utf-8').splitlines()))}
    picks = set()
    for src, k, issue, _ in main():
        if src not in MODULES:
            continue  # scenarios are fixed through tools.scenarios
        if issue.startswith('latin-leftover:') and set(issue.split(':', 1)[1].split(',')) <= LEGIT_LATIN:
            continue
        picks.add((src, k))
    picks |= {tuple(x.split(':', 1)) for x in TERM_REVIEW}
    rows = []
    for m, k in sorted(picks - queued):
        rows.append({'module': m, 'key': k, 'en': read_en(m)[k], 'hint': read_cfg(SRC / f'{m}.cfg')[k],
                     'reason': 'review (fix reversed line / leftover English / cliff = جرف، أجراف)'})
    with open(todo_path, 'a', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    return rows


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--requeue' in sys.argv:
        for r in requeue():
            print('requeued', r['module'], r['key'])
    else:
        for s, k, i, t in main()[:60]:
            print(f'{s} | {k} | {i} | {t[:60]}')
