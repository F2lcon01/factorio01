"""Arabic for the other mods a player installs: a local, data-only mod 'arabic-mods-local' generated from their
English locale (the game falls back to English for every key no Arabic file defines; arabic-complete only covers the
base game). Each string takes the first that applies:
  manual override (modpack_overrides.json) > cache (same English) > Arabic the mod ships, if valid >
  brand/abbreviation kept as is > the same English already translated in our 7,600 strings >
  machine translation (tools.translator, any provider's API key) > none: the game keeps showing English.
Every Arabic value passes tools.lint.check_value (placeholders, tags, plurals) and is shaped by tools.build.
The pack declares an optional dependency on each mod it translates, so it loads after them and wins over any
unshaped Arabic they ship. Local only: other people's mod texts are not published.
python -E -m tools.modpack build [--offline]   → dist/arabic-mods-local_1.0.0, reports/modpack.md, one JSON line
python -E -m tools.modpack status              → {"fingerprint", "changed", "pending"} for tools/auto_update.ps1"""
import hashlib, heapq, json, os, re, shutil, sys, time, unicodedata, zipfile
from pathlib import Path
from tools import translator
from tools.build import game_version, visual_value
from tools.cfg import parse_cfg, write_cfg
from tools.corrections import normalize
from tools.lint import TOKEN_RE, check_value
from tools.paths import DIST, MODULES, REPORTS, ROOT, SRC, WORK, read_en
from tools.textfx import from_visual

PACK, PACK_VERSION = 'arabic-mods-local', '1.0.0'
NOT_TRANSLATED = set(MODULES) | {'arabic-complete', 'arabic-crowdin', PACK}
STATE = WORK / 'modpack'
OVERRIDES = ROOT / 'modpack_overrides.json'
DEP_RE = re.compile(r'^\s*(\(\?\)|\?|!|~)?\s*([^<>=]+?)\s*(?:[<>=].*)?$')
BIDI_RE = re.compile('[‎‏‪-‮⁦-⁩]')
WORD_RE = re.compile('[ء-ي]{2,}')
LUA_LITERAL_RE = re.compile(r'\b(caption|tooltip)\s*=\s*"([^"]*[A-Za-z]{3,}[^"]*)"')
LUA_KEY_RE = re.compile(r'\{\s*"([a-z0-9_-]+)\.([A-Za-z0-9_.-]+)"')
BATCH_STRINGS, BATCH_CHARS = 40, 4000


def mods_dir():
    return Path(os.environ.get('FA_MODS_DIR') or Path(os.environ['APPDATA']) / 'Factorio' / 'mods')


def _version_key(v):
    return tuple(int(x) if x.isdigit() else 0 for x in str(v).split('.'))


# ---------- reading installed mods (folders or zips) ----------
def read_mod(path: Path) -> dict:
    """{'name', 'version', 'deps', 'locale': {lang: {key: text}}, 'lua': [text]} from a mod folder or zip."""
    files = {}
    if path.is_dir():
        for f in path.rglob('*'):
            if f.is_file() and f.suffix in ('.json', '.cfg', '.lua'):
                files[f.relative_to(path).as_posix()] = f.read_text(encoding='utf-8-sig', errors='replace')
    else:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                parts = n.split('/', 1)
                if len(parts) == 2 and parts[1] and n.endswith(('.json', '.cfg', '.lua')):
                    files[parts[1]] = z.read(n).decode('utf-8-sig', errors='replace')
    info = json.loads(files['info.json'])
    locale = {}
    for rel, text in files.items():
        m = re.fullmatch(r'locale/([^/]+)/[^/]+\.cfg', rel)
        if m:
            locale.setdefault(m.group(1), {}).update(parse_cfg(text))
    return {'name': info['name'], 'version': info.get('version', '0.0.0'), 'deps': info.get('dependencies', []),
            'locale': locale, 'lua': [t for r, t in files.items() if r.endswith('.lua')]}


def enabled_mods(directory: Path) -> list[dict]:
    """The enabled third-party mods, newest installed version of each."""
    listing = json.loads((directory / 'mod-list.json').read_text(encoding='utf-8-sig'))
    enabled = {m['name'] for m in listing['mods'] if m.get('enabled')} - NOT_TRANSLATED
    found = {}
    for p in directory.iterdir():
        if not (p.is_dir() and (p / 'info.json').exists()) and p.suffix != '.zip':
            continue
        name = re.sub(r'_\d+\.\d+\.\d+$', '', p.stem if p.suffix == '.zip' else p.name)
        if name not in enabled:
            continue
        try:
            mod = read_mod(p)
        except (KeyError, ValueError, zipfile.BadZipFile):
            continue   # not a readable mod: the game will complain about it, not us
        if mod['name'] in enabled and (mod['name'] not in found
                                       or _version_key(mod['version']) > _version_key(found[mod['name']]['version'])):
            found[mod['name']] = mod
    return list(found.values())


def load_order(mods: list[dict]) -> list[dict]:
    """Dependencies first (required and optional ones), ties by name: later mods override earlier locale keys."""
    by_name = {m['name']: m for m in mods}
    after = {n: set() for n in by_name}
    for m in mods:
        for d in m['deps']:
            g = DEP_RE.match(d)
            if g and g.group(1) not in ('!', '~') and g.group(2) in by_name:
                after[m['name']].add(g.group(2))
    ready = [(n.lower(), n) for n, deps in after.items() if not deps]
    heapq.heapify(ready)
    out, done = [], set()
    while ready:
        _, n = heapq.heappop(ready)
        out.append(by_name[n])
        done.add(n)
        for other, deps in after.items():
            if other not in done and n in deps and deps <= done and all(o != other for _, o in ready):
                heapq.heappush(ready, (other.lower(), other))
    out += [by_name[n] for n in sorted(set(by_name) - done, key=str.lower)]   # dependency cycle: keep them anyway
    return out


# ---------- choosing the Arabic for each key ----------
def _sha(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def _load_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _vocabulary():
    words = set()
    for m in MODULES:
        p = SRC / f'{m}.cfg'
        if p.exists():
            words.update(WORD_RE.findall(p.read_text(encoding='utf-8')))
    return words


def translation_memory():
    """English text (case-insensitive) → our Arabic, from the base-game translation."""
    tm = {}
    for m in MODULES:
        p = SRC / f'{m}.cfg'
        if not p.exists():
            continue
        ar = parse_cfg(p.read_text(encoding='utf-8'))
        for k, e in read_en(m).items():
            if k in ar:
                tm.setdefault(e.strip().lower(), ar[k])
    return tm


def orient(text, vocab):
    """Arabic a mod ships may be logical, reversed or pre-shaped: return normal text, or None if unreadable."""
    t = BIDI_RE.sub('', unicodedata.normalize('NFKC', text))
    best, score = None, 0.0
    for cand in (t, from_visual(t)):
        words = WORD_RE.findall(cand)
        s = sum(w in vocab for w in words) / len(words) if words else 0.0
        if s > score:
            best, score = cand, s
    return best if score >= 0.34 else None


def is_brand(en):
    """Nothing to translate: abbreviations, product names, numbers ('P.U.M.P.', 'OK', 'MK2')."""
    return not re.search(r'[a-z]{2,}', TOKEN_RE.sub('', en))


def clean(ar):
    return normalize(BIDI_RE.sub('', ar)).strip()


def glossary_for(texts, glossary):
    low = ' '.join(texts).lower()
    hits = {t: a for t, a in glossary.items() if len(t) > 2 and re.search(rf'(?<![a-z]){re.escape(t)}(?![a-z])', low)}
    return dict(sorted(hits.items(), key=lambda x: -len(x[0]))[:60])


def batches(items):
    batch, size = {}, 0
    for k, e in items:
        if batch and (len(batch) >= BATCH_STRINGS or size + len(e) > BATCH_CHARS):
            yield batch
            batch, size = {}, 0
        batch[k] = e
        size += len(e)
    if batch:
        yield batch


def resolve(mods, *, tm, vocab, cache, overrides, glossary, translate=None, log=print):
    """→ (arabic {key: logical}, owner {key: mod}, rows for the report)."""
    base_keys = set().union(*(read_en(m).keys() for m in MODULES))
    en, owner, mod_ar, conflicts = {}, {}, {}, []
    for m in mods:
        for k, e in m['locale'].get('en', {}).items():
            if k in base_keys:
                continue   # base-game key: arabic-complete already translates it
            if k in en and en[k] != e:
                conflicts.append((k, owner[k], m['name']))
            en[k], owner[k] = e, m['name']
        mod_ar.update(m['locale'].get('ar', {}))
    arabic, source, pending = {}, {}, []
    for k, e in en.items():
        c = cache.get(k)
        shipped = orient(mod_ar[k], vocab) if k in mod_ar else None
        if k in overrides:
            arabic[k], source[k] = overrides[k], 'override'
        elif c and c['en'] == _sha(e) and not check_value(e, c['ar']):
            arabic[k], source[k] = c['ar'], c['src']
        elif shipped and not check_value(e, shipped):
            arabic[k], source[k] = shipped, 'mod-arabic'
        elif is_brand(e):
            source[k] = 'brand'   # the game shows the English, which is the right text here
        elif e.strip().lower() in tm and not check_value(e, tm[e.strip().lower()]):
            arabic[k], source[k] = tm[e.strip().lower()], 'memory'
        else:
            pending.append(k)
    if pending and translate:
        todo = sorted(pending, key=lambda k: (owner[k], k))
        for attempt in (1, 2):   # the second pass retries what failed validation once
            failed = []
            for batch in batches((k, en[k]) for k in todo):
                try:
                    got = translate(batch, glossary_for(batch.values(), glossary))
                except translator.TranslatorError as e:
                    log(f'translation batch failed: {e}')
                    failed += list(batch)
                    continue
                for k in batch:
                    ar = clean(got.get(k, ''))
                    if ar and not check_value(en[k], ar):
                        arabic[k], source[k] = ar, 'machine'
                        cache[k] = {'en': _sha(en[k]), 'ar': ar, 'src': 'machine'}
                    else:
                        failed.append(k)
            todo = failed
            if not todo:
                break
        pending = todo
    for k in pending:
        source[k] = 'english'
    return arabic, owner, {'en': en, 'source': source, 'conflicts': conflicts}


# ---------- the pack ----------
def build_pack(mods, arabic, owner, en, out_root=DIST) -> Path:
    pack = Path(out_root) / f'{PACK}_{PACK_VERSION}'
    if pack.exists():
        shutil.rmtree(pack)   # build output only
    order = {m['name']: list(m['locale'].get('en', {})) for m in mods}
    by_owner = {}
    for k, ar in arabic.items():
        by_owner.setdefault(owner[k], {})[k] = visual_value(k, ar)
    for name, values in by_owner.items():
        write_cfg(pack / 'locale' / 'ar' / f'{name}.cfg', values, order[name])
    major_minor = '.'.join(game_version().split('.')[:2])
    info = {'name': PACK, 'version': PACK_VERSION, 'title': 'Arabic for installed mods (generated locally)',
            'author': 'factorio-arabic', 'factorio_version': major_minor,
            'description': 'Arabic, shaped and ordered for the engine, for the other mods installed here. '
                           'Rebuilt by tools/translate_mods.ps1; not for distribution.',
            'dependencies': [f'base >= {major_minor}.0', '? arabic-complete'] + [f'? {n}' for n in sorted(by_owner)]}
    pack.mkdir(parents=True, exist_ok=True)
    (pack / 'info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    return pack


def lua_findings(mods, en_keys):
    """Texts no locale file can reach: hard-coded captions, and keys the code uses that no locale defines."""
    out = []
    for m in mods:
        own_sections = {k.split('/', 1)[0] for k in m['locale'].get('en', {})}
        for text in m['lua']:
            for kind, literal in LUA_LITERAL_RE.findall(text):
                out.append((m['name'], f'hard-coded {kind}', literal))
            for sec, key in LUA_KEY_RE.findall(text):
                if sec in own_sections and f'{sec}/{key}' not in en_keys:
                    out.append((m['name'], 'key missing even in English', f'{sec}.{key}'))
    return sorted(set(out))


def fingerprint(mods):
    parts = sorted(f"{m['name']}@{m['version']}" for m in mods)
    if OVERRIDES.exists():
        parts.append(_sha(OVERRIDES.read_text(encoding='utf-8')))
    return _sha('|'.join(parts))


def report(mods, rows, findings, provider):
    counts = {}
    for k, src in rows['source'].items():
        counts.setdefault(rows['owner'][k], {}).setdefault(src, 0)
        counts[rows['owner'][k]][src] += 1
    kinds = ['override', 'machine', 'mod-arabic', 'memory', 'brand', 'english']
    lines = [f'# Arabic for installed mods — {time.strftime("%Y-%m-%d %H:%M")}', '',
             f'Translator: {provider}', '', '| mod | ' + ' | '.join(kinds) + ' |', '|---|' + '---|' * len(kinds)]
    for m in mods:
        c = counts.get(m['name'], {})
        lines.append(f"| {m['name']} {m['version']} | " + ' | '.join(str(c.get(k, 0)) for k in kinds) + ' |')
    left = sorted(k for k, s in rows['source'].items() if s == 'english')
    if left:
        lines += ['', '## Still in English', ''] + [f'- `{rows["owner"][k]}` `{k}`: {rows["en"][k][:80]}' for k in left]
    if rows['conflicts']:
        lines += ['', '## Same key in several mods (the last loaded wins)', '']
        lines += [f'- `{k}`: {a} → {b}' for k, a, b in rows['conflicts']]
    if findings:
        lines += ['', '## Out of reach of locale files', ''] + [f'- `{n}` {kind}: `{t}`' for n, kind, t in findings]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'modpack.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def _translator(offline, log):
    key = os.environ.get('FA_TRANSLATE_KEY', '')
    if offline or not key:
        return None, 'none (offline)'
    STATE.mkdir(parents=True, exist_ok=True)
    saved = _load_json(STATE / 'translator.json', {})
    tag = _sha(key)[:12] + '|' + '|'.join(os.environ.get(v, '') for v in
                                          ('FA_TRANSLATE_PROVIDER', 'FA_TRANSLATE_BASE_URL', 'FA_TRANSLATE_MODEL'))
    cfg = saved.get('config') if saved.get('tag') == tag else None
    if not cfg:
        cfg = translator.detect(key)   # raises TranslatorError: the caller reports it
        (STATE / 'translator.json').write_text(json.dumps({'tag': tag, 'config': cfg}, indent=1), encoding='utf-8')
    log(f"translator: {cfg['provider']} / {cfg['model']}")
    return (lambda batch, gloss: translator.translate(cfg, key, batch, gloss)), f"{cfg['provider']} / {cfg['model']}"


def build(offline=False, log=print):
    mods = load_order(enabled_mods(mods_dir()))
    STATE.mkdir(parents=True, exist_ok=True)
    cache = _load_json(STATE / 'cache.json', {})
    translate, provider = _translator(offline, log)
    arabic, owner, rows = resolve(
        mods, tm=translation_memory(), vocab=_vocabulary(), cache=cache, overrides=_load_json(OVERRIDES, {}),
        glossary=_load_json(ROOT / 'glossary.json', {}), translate=translate, log=log)
    rows['owner'] = owner
    (STATE / 'cache.json').write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding='utf-8')
    pack = build_pack(mods, arabic, owner, rows['en'])
    pending = sum(s == 'english' for s in rows['source'].values())
    report(mods, rows, lua_findings(mods, set(rows['en']) | set().union(*(read_en(m) for m in MODULES))), provider)
    (STATE / 'state.json').write_text(json.dumps({'fingerprint': fingerprint(mods), 'pending': pending,
                                                  'built_at': time.strftime('%Y-%m-%dT%H:%M:%S')}), encoding='utf-8')
    return {'pack': pack.name, 'mods': len(mods), 'strings': len(rows['en']), 'arabic': len(arabic),
            'english_left': pending, 'translator': provider}


def status():
    mods = load_order(enabled_mods(mods_dir()))
    saved = _load_json(STATE / 'state.json', {})
    fp = fingerprint(mods)
    return {'fingerprint': fp, 'changed': fp != saved.get('fingerprint'), 'pending': saved.get('pending', 0),
            'mods': len(mods)}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'build':
        try:
            print(json.dumps(build(offline='--offline' in sys.argv, log=lambda s: print(s, file=sys.stderr))))
        except translator.TranslatorError as e:
            sys.exit(f'translator: {e}')
    elif cmd == 'status':
        print(json.dumps(status()))
    else:
        sys.exit('usage: python -E -m tools.modpack build [--offline] | status')
