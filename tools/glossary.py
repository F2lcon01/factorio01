"""Build glossary.json {english term (lower): arabic logical} from translated prototype names.
--apply-decisions: rewrite every name key whose English matches a term in glossary_decisions.json."""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.paths import MODULES, ROOT, SRC, read_en

NAME_SECTIONS = {'item-name', 'entity-name', 'fluid-name', 'technology-name', 'recipe-name', 'tile-name',
                 'space-location-name', 'item-group-name', 'equipment-name', 'virtual-signal-name',
                 'quality-name', 'map-gen-preset-name', 'asteroid-chunk-name', 'surface-name'}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    gl, conflicts = {}, []
    for m in MODULES:
        en, ar = read_en(m), read_cfg(SRC / f'{m}.cfg')
        for k, e in en.items():
            if k.split('/', 1)[0] in NAME_SECTIONS and k in ar and '__' not in e:
                term = e.strip().lower()
                if term in gl and gl[term] != ar[k]:
                    conflicts.append(f'{term}: {gl[term]} | {ar[k]}')
                gl.setdefault(term, ar[k])
    (ROOT / 'glossary.json').write_text(json.dumps(gl, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')
    print(len(gl), 'terms;', len(conflicts), 'conflicts')
    for c in conflicts[:50]:
        print('  CONFLICT', c)


def apply_decisions():
    decisions = json.loads((ROOT / 'glossary_decisions.json').read_text(encoding='utf-8'))
    changed = 0
    for m in MODULES:
        en, ar = read_en(m), read_cfg(SRC / f'{m}.cfg')
        for k, e in en.items():
            term = e.strip().lower()
            if k.split('/', 1)[0] in NAME_SECTIONS and k in ar and term in decisions and ar[k] != decisions[term]:
                ar[k] = decisions[term]
                changed += 1
        write_cfg(SRC / f'{m}.cfg', ar, list(en))
    print('name keys rewritten:', changed)


if __name__ == '__main__':
    if '--apply-decisions' in sys.argv:
        apply_decisions()
    main()
