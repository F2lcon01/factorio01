"""Sample translated keys for human review: reports/review-NNN.md (key | English | Arabic).
python -E -m tools.review NNN [count]   — NNN = batch id or 'terms'"""
import json, random, sys
from tools.paths import REPORTS, WORK


def sample(n, count=20, seed=7):
    if n == 'terms':
        src = WORK / 'terms' / 'terms.jsonl'
        out = WORK / 'terms' / 'terms.out.jsonl'
    else:
        src, out = WORK / 'batches' / f'{n}.jsonl', WORK / 'out' / f'{n}.jsonl'
    a = [json.loads(l) for l in src.read_text(encoding='utf-8').splitlines() if l.strip()]
    b = [json.loads(l) for l in out.read_text(encoding='utf-8').splitlines() if l.strip()]
    pairs = list(zip(a, b))
    random.Random(seed).shuffle(pairs)
    rows = [f"| `{s.get('key', '')}` | {s['en'][:140]} | {o['ar'][:140]} |" for s, o in pairs[:count]]
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f'review-{n}.md'
    path.write_text('| key | English | العربية |\n|---|---|---|\n' + '\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    return path


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = sample(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    print(p.read_text(encoding='utf-8'))
