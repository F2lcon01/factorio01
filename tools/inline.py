"""Inline translation helpers (no JSON escaping by hand).
python -E -m tools.inline show NNN   — compact view: glossary terms + 'key ⟶ English [| hint]'
python -E -m tools.inline pack NNN   — work/inline/NNN.tsv ('key=arabic' per line, cfg-style; keys never
                                       contain '=') → work/out/NNN.jsonl"""
import json, sys
from tools.paths import WORK


def _rows(n):
    return [json.loads(l) for l in (WORK / 'batches' / f'{n}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]


def show(n):
    gl = json.loads((WORK / 'batches' / f'{n}.glossary.json').read_text(encoding='utf-8'))
    print('GLOSSARY:', '; '.join(f'{k}={v}' for k, v in gl.items()))
    for r in _rows(n):
        hint = f"  ‖ HINT[{r['reason'][:6]}]: {r['hint']}" if r['hint'] else ''
        print(f"{r['key']} ⟶ {r['en']}{hint}")


def pack(n):
    rows = _rows(n)
    tsv = {}
    for line in (WORK / 'inline' / f'{n}.tsv').read_text(encoding='utf-8').splitlines():
        if line.strip():
            k, _, ar = line.partition('=')
            tsv[k] = ar
    missing = [r['key'] for r in rows if r['key'] not in tsv]
    if missing:
        raise SystemExit(f'missing {len(missing)} keys, e.g. {missing[:5]}')
    (WORK / 'out').mkdir(exist_ok=True)
    (WORK / 'out' / f'{n}.jsonl').write_text(
        '\n'.join(json.dumps({'module': r['module'], 'key': r['key'], 'ar': tsv[r['key']]}, ensure_ascii=False)
                  for r in rows) + '\n', encoding='utf-8', newline='\n')
    print('packed', len(rows))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    {'show': show, 'pack': pack}[sys.argv[1]](sys.argv[2])
