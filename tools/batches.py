"""Split work/todo.jsonl into batches of 120, grouped by module+section, with per-batch glossary."""
import json, re
from tools.paths import ROOT, WORK

SIZE = 120


def main():
    todo = [json.loads(l) for l in (WORK / 'todo.jsonl').read_text(encoding='utf-8').splitlines() if l]
    todo.sort(key=lambda t: (t['module'], t['key']))
    gl = json.loads((ROOT / 'glossary.json').read_text(encoding='utf-8'))
    out = WORK / 'batches'; out.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(todo), SIZE):
        chunk = todo[i:i + SIZE]
        text = ' '.join(t['en'].lower() for t in chunk)
        terms = {k: v for k, v in gl.items() if re.search(rf'\b{re.escape(k)}\b', text)}
        n = i // SIZE + 1
        (out / f'{n:03}.jsonl').write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in chunk) + '\n', encoding='utf-8')
        (out / f'{n:03}.glossary.json').write_text(json.dumps(terms, ensure_ascii=False, indent=1), encoding='utf-8')
    print((len(todo) + SIZE - 1) // SIZE, 'batches')


if __name__ == '__main__':
    main()
