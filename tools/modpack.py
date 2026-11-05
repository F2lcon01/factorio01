"""Arabic for the other mods a player installs: a local, data-only mod 'arabic-mods-local' generated from their
English locale (the game falls back to English for every key no Arabic file defines; arabic-complete only covers the
base game). Each string takes the first that applies:
  manual override > Arabic the mod ships, if valid > brand/abbreviation kept as is >
  base-game memory (our 7,600 strings) > shared translation memory (every string ever translated, any mod) >
  machine translation (tools.translator, any provider's API key; the result enters the shared memory) > English.
A mod that did not change therefore costs no API request, and an updated mod only sends its new or changed strings.
Every Arabic value passes tools.lint.check_value (placeholders, tags, plurals) and is shaped by tools.build.
The pack declares an optional dependency on each mod it translates, so it loads after them and wins over any
unshaped Arabic they ship. Local only: other people's mod texts are not published.
State (FA_STATE_DIR, default work/modpack): memory.json, manifest.json, usage.json, last_run.json, translator.json.
python -E -m tools.modpack build [--offline]   → dist/arabic-mods-local_1.0.0, reports/modpack.md, one JSON line
python -E -m tools.modpack status              → fingerprint, changed, pending, and the state of every mod
python -E -m tools.modpack summary             → the last run (strings, requests, tokens, memory hits, savings)
python -E -m tools.modpack original <mod>      → keep that mod in its original language (arabic <mod> undoes it)
FA_PROGRESS_FILE: JSON lines {"stage", "done", "total"} for the window's progress bar."""
import hashlib, heapq, json, os, re, shutil, sys, time, unicodedata, zipfile
from pathlib import Path
from tools import memory, translator
from tools.build import game_version, visual_value
from tools.cfg import parse_cfg, write_cfg
from tools.corrections import normalize
from tools.lint import TOKEN_RE, check_value
from tools.paths import DIST, MODULES, REPORTS, ROOT, SRC, WORK, read_en
from tools.textfx import from_visual

PACK, PACK_VERSION = 'arabic-mods-local', '1.0.0'
NOT_TRANSLATED = set(MODULES) | {'arabic-complete', 'arabic-crowdin', PACK}
BUILTIN = {'base', 'elevated-rails', 'quality', 'recycler', 'space-age'}   # ship with the game (DLC ones when enabled)
STATE = Path(os.environ.get('FA_STATE_DIR') or WORK / 'modpack')
DEP_RE = re.compile(r'^\s*(\(\?\)|\?|!|~)?\s*([^<>=]+?)\s*(?:[<>=].*)?$')
DEP_NAME_RE = re.compile(r'[A-Za-z0-9_-]+')   # the mod portal's name rule: safe inside a dependency string
BIDI_RE = re.compile('[‎‏‪-‮⁦-⁩]')
WORD_RE = re.compile('[ء-ي]{2,}')
LUA_LITERAL_RE = re.compile(r'\b(caption|tooltip)\s*=\s*"([^"]*[A-Za-z]{3,}[^"]*)"')
LUA_KEY_RE = re.compile(r'\{\s*"([a-z0-9_-]+)\.([A-Za-z0-9_.-]+)"')
BATCH_STRINGS, BATCH_CHARS = 40, 4000
STATES_AR = {'translated': 'مترجم', 'new': 'جديد', 'changed': 'تغيّر', 'pending': 'ينتظر الترجمة',
             'original': 'بلغته الأصلية', 'empty': 'لا نصوص فيه',
             # the game will not load these: nothing is sent for them
             'disabled': 'معطّل في اللعبة', 'incompatible': 'لا يعمل مع إصدار لعبتك', 'missing-dep': 'ينقصه'}


def mods_dir():
    return Path(os.environ.get('FA_MODS_DIR') or Path(os.environ['APPDATA']) / 'Factorio' / 'mods')


def overrides_path():
    """Project file for the developer; the player's state folder otherwise (it survives tool updates)."""
    if os.environ.get('FA_OVERRIDES'):
        return Path(os.environ['FA_OVERRIDES'])
    return ROOT / 'modpack_overrides.json' if SRC.exists() else STATE / 'overrides.json'


def _version_key(v):
    return tuple(int(x) if x.isdigit() else 0 for x in str(v).split('.'))


def _sha(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def _load_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(tmp, path)   # atomic


def progress(stage, done, total):
    p = os.environ.get('FA_PROGRESS_FILE')
    if p:
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'stage': stage, 'done': done, 'total': total}) + '\n')


# ---------- reading installed mods (folders or zips) ----------
def read_mod(path: Path) -> dict:
    """{'name', 'title', 'version', 'deps', 'locale': {lang: {key: text}}, 'lua': [text]} from a folder or zip."""
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
    return {'name': info['name'], 'title': info.get('title', info['name']), 'version': info.get('version', '0.0.0'),
            'factorio_version': str(info.get('factorio_version', '')), 'deps': info.get('dependencies', []),
            'locale': locale, 'lua': [t for r, t in files.items() if r.endswith('.lua')]}


def _required(mod):
    """Names of the mods this one cannot load without ('~' is required too, it only skips load ordering)."""
    out = []
    for d in mod['deps']:
        g = DEP_RE.match(d)
        if g and g.group(1) in (None, '~'):
            out.append(g.group(2))
    return out


def _game_major_minor():
    try:
        return '.'.join(game_version().split('.')[:2])
    except (OSError, KeyError, ValueError):
        return None   # no game data here: do not judge compatibility


def scan_mods(directory: Path, game_mm=None):
    """Every third-party mod in the folder as the game will see it on its next start → (usable, skipped).
    The internal name comes from info.json (folders like 'Flow Control' carry no version). A mod that mod-list.json
    does not mention yet counts as enabled: the game adds a newly copied mod enabled when it starts. Skipped, with the
    reason, because the game will not load them: 'disabled' in mod-list.json, 'incompatible' (factorio_version is
    not the game's major.minor), 'missing-dep' (a required mod is absent, disabled or itself skipped)."""
    listing = directory / 'mod-list.json'
    state = {m['name']: bool(m.get('enabled')) for m in
             (json.loads(listing.read_text(encoding='utf-8-sig'))['mods'] if listing.exists() else [])}
    found, others = {}, set()
    for p in directory.iterdir():
        if not (p.is_dir() and (p / 'info.json').exists()) and p.suffix != '.zip':
            continue
        try:
            mod = read_mod(p)
        except (KeyError, ValueError, OSError, zipfile.BadZipFile):
            continue   # not a readable mod: the game will complain about it, not us
        n = mod['name']
        if n in NOT_TRANSLATED:
            others.add(n)
        elif n not in found or _version_key(mod['version']) > _version_key(found[n]['version']):
            found[n] = mod
    usable, skipped = {}, []
    for n, m in found.items():
        m['listed'] = n in state
        if state.get(n, True) is False:
            skipped.append({'mod': m, 'reason': 'disabled', 'detail': ''})
        elif game_mm and m['factorio_version'] and m['factorio_version'] != game_mm:
            skipped.append({'mod': m, 'reason': 'incompatible', 'detail': m['factorio_version']})
        else:
            usable[n] = m
    loaded = {b for b in BUILTIN if state.get(b, b == 'base')} | {n for n in others if state.get(n, True)}
    changed = True
    while changed:   # a mod whose required mod is skipped is skipped too
        changed = False
        for n, m in list(usable.items()):
            missing = [d for d in _required(m) if d not in usable and d not in loaded]
            if missing:
                skipped.append({'mod': m, 'reason': 'missing-dep', 'detail': ', '.join(missing)})
                del usable[n]
                changed = True
    return list(usable.values()), sorted(skipped, key=lambda s: s['mod']['name'].lower())


def enabled_mods(directory: Path) -> list[dict]:
    """The third-party mods the game will load, newest installed version of each."""
    return scan_mods(directory, _game_major_minor())[0]


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


SOURCE_LANGS = ['en', 'en-GB', 'de', 'fr', 'es-ES', 'pt-BR', 'pt-PT', 'it', 'ru', 'pl', 'nl', 'cs', 'uk', 'tr',
                'zh-CN', 'zh-TW', 'ja', 'ko']   # a key with no English is taken from the first of these the mod has


def source_locale(mod):
    """→ ({key: source text}, {key: language} for the keys that are not English). The game falls back to English
    only, so a key a mod ships in Portuguese alone (pole_range_plus, roboports_mc, turbo_player) reaches an Arabic
    player as 'Unknown key'. Such keys are translated from the language the mod has; the translator is told which.
    English always wins, even an empty English value (the author meant it)."""
    loc = mod['locale']
    order = [l for l in SOURCE_LANGS if l in loc] + sorted(l for l in loc if l not in SOURCE_LANGS and l != 'ar')
    text, lang = {}, {}
    for l in order:
        for k, v in loc[l].items():
            if k not in text and (l == 'en' or v.strip()):
                text[k] = v
                if l != 'en':
                    lang[k] = l
    return text, lang


def merge(mods):
    """Winning source text per key (last loaded wins): English, or another language the mod ships when it has no
    English for that key; its owner, Arabic the mods ship, key clashes, and {key: language} for non-English sources."""
    base_keys = set().union(*(read_en(m).keys() for m in MODULES))
    en, owner, mod_ar, conflicts, lang = {}, {}, {}, [], {}
    for m in mods:
        text, langs = source_locale(m)
        for k, e in text.items():
            if k in base_keys:
                continue   # base-game key: arabic-complete already translates it
            if k in en and en[k] != e:
                conflicts.append((k, owner[k], m['name']))
            en[k], owner[k] = e, m['name']
            if k in langs:
                lang[k] = langs[k]
            else:
                lang.pop(k, None)
        mod_ar.update(m['locale'].get('ar', {}))
    return en, owner, mod_ar, conflicts, lang


# ---------- choosing the Arabic for each key ----------
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


def excluded() -> set:
    """Mods the player keeps in their original language (the window's checkboxes): not translated, not packed."""
    return set(_load_json(STATE / 'excluded.json', []))


def set_excluded(name: str, keep_original: bool) -> list:
    names = excluded() | {name} if keep_original else excluded() - {name}
    _save_json(STATE / 'excluded.json', sorted(names))
    return sorted(names)


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


def resolve(mods, *, base, memory_, overrides, terms, translate=None, model='', log=print, keep=frozenset(),
            should_stop=None):
    """→ (arabic {key: logical}, owner {key: mod}, rows). memory_ is a tools.memory.TranslationMemory; translate is
    (batch {key: English}, terms) → ({key: Arabic}, usage). Machine results enter the shared memory.
    keep: mods kept in their original language; an override of null keeps one string original. Either way nothing is
    sent or written for them, and their stored translations stay in the memory for when they are switched back."""
    en, owner, mod_ar, conflicts, lang = merge(mods)
    vocab = {w for v in base.values() for w in WORD_RE.findall(v)}
    arabic, source, pending, review, flags, errors = {}, {}, [], [], [], []
    for k, e in en.items():
        if owner[k] in keep or (k in overrides and overrides[k] is None):
            source[k] = 'original'
            continue
        shipped = orient(mod_ar[k], vocab) if k in mod_ar else None
        from_base, hit = base.get(memory.norm(e).lower()), memory_.entry(e)
        from_mem = hit['ar'] if hit else None
        if hit and hit.get('ctx') and hit['ctx'] != f'{owner[k]}|{k}' and k not in overrides:
            review.append((k, hit['ctx']))   # same English, another key or mod: reused, listed for a look
        if k in overrides:
            arabic[k], source[k] = overrides[k], 'override'
        elif shipped and not check_value(e, shipped):
            arabic[k], source[k] = shipped, 'mod-arabic'
        elif is_brand(e):
            source[k] = 'brand'   # the game shows the English, which is the right text here
        elif from_base and not check_value(e, from_base):
            arabic[k], source[k] = from_base, 'memory-base'
        elif from_mem and not check_value(e, from_mem):
            arabic[k], source[k] = from_mem, 'memory'
        else:
            pending.append(k)
    usage = translator.new_usage()
    stopped = paused = False   # paused: the player asked (should_stop), checked between batches, never mid-batch
    if pending and translate:
        same = {}   # the same English in several keys or mods is sent once, then applied to all of them
        for k in sorted(pending, key=lambda k: (owner[k], k)):
            same.setdefault(memory.norm(en[k]).lower(), []).append(k)
        todo = [keys[0] for keys in same.values()]
        total, done, busy_in_a_row = len(todo), 0, 0
        progress('translate', 0, total)
        for _ in (1, 2):   # the second pass retries once what failed validation
            failed = []
            # one source language per batch, English first: the translator is told the language it reads
            sources = sorted({lang.get(k, 'en') for k in todo}, key=lambda l: (l != 'en', l))
            for src, batch in ((s, b) for s in sources for b in batches((k, en[k]) for k in todo
                                                                         if lang.get(k, 'en') == s)):
                if not stopped and should_stop and should_stop():
                    stopped = paused = True
                    log('paused by the player: the rest is translated on the next run')
                if stopped:
                    failed += list(batch)
                    continue
                batch_terms = memory.terms_for(batch.values(), terms) if src == 'en' else {}   # English glossary
                try:
                    got, u = translate(batch, batch_terms, src)
                    translator.add_usage(usage, u)
                except translator.TranslatorError as e:
                    log(f'translation batch failed: {e}')
                    errors.append(str(e))   # shown to the player: the strings stay English for this reason
                    failed += list(batch)
                    busy_in_a_row = busy_in_a_row + 1 if getattr(e, 'busy', False) else 0
                    # every fallback model is busy or out of quota: the rest of this run would fail the same way.
                    # Stop; what was translated is in the memory, and the next run continues from here.
                    stopped = busy_in_a_row >= 2
                    continue
                busy_in_a_row = 0
                for k in batch:
                    ar = clean(got.get(k, ''))
                    if ar and ar != en[k].strip() and not check_value(en[k], ar):   # a copy of the source is no answer
                        flags += [(k, f) for f in quality_flags(en[k], ar, batch_terms)]
                        memory_.put(en[k], ar, 'machine', model, ctx=f'{owner[k]}|{k}')
                        for twin in same[memory.norm(en[k]).lower()]:
                            arabic[twin], source[twin] = ar, 'machine'
                        done += 1
                    else:
                        failed.append(k)
                memory_.save()   # each answered batch is kept, even if the run is closed or stopped later
                progress('translate', min(done, total), total)
            todo = failed
            if not todo or stopped:
                break
        pending = [twin for k in todo for twin in same[memory.norm(en[k]).lower()]]
    for k in pending:
        source[k] = 'english'
    return arabic, owner, {'en': en, 'owner': owner, 'source': source, 'conflicts': conflicts, 'usage': usage,
                           'review': review, 'flags': flags, 'errors': errors, 'stopped': stopped, 'paused': paused,
                           'lang': lang}


def quality_flags(en, ar, terms):
    """Warnings, not rejections (placeholders, tags and plurals are already enforced by check_value):
    a glossary term the translation did not use, and an answer far longer than the English."""
    out = []
    low = en.lower()
    for t, a in terms.items():
        if re.search(rf'(?<![a-z]){re.escape(t)}(?![a-z])', low) and a not in ar:
            out.append(f'مصطلح المسرد لم يُستخدم: {t} ← {a}')
    if len(ar) > 3 * len(en) + 20:
        out.append('الترجمة أطول بكثير من الأصل')
    return out


# ---------- per-mod state ----------
def mod_fingerprint(mod):
    return _sha(mod['version'] + '\n' + '\n'.join(f'{k}={v}' for k, v in sorted(source_locale(mod)[0].items())))


def mod_states(mods, rows, manifest, keep=frozenset()):
    out = []
    for m in mods:
        keys = [k for k, o in rows['owner'].items() if o == m['name']]
        src = [rows['source'][k] for k in keys]
        rec = manifest.get(m['name'])
        changed = [k for k in keys if not rec or rec.get('keys', {}).get(k) != _sha(rows['en'][k])]
        pending, original = src.count('english'), src.count('original')
        state = 'original' if m['name'] in keep else 'empty' if not keys else 'new' if not rec else \
            'changed' if rec.get('fp') != mod_fingerprint(m) else 'pending' if pending else 'translated'
        out.append({'name': m['name'], 'title': m['title'], 'version': m['version'], 'strings': len(keys),
                    'arabic': len(keys) - pending - original - src.count('brand'), 'brand': src.count('brand'),
                    'original': original, 'pending': pending, 'changed': len(changed), 'excluded': m['name'] in keep,
                    'state': state, 'state_ar': STATES_AR[state], 'detail': ''})
    return out


def skipped_states(skipped):
    """Rows for the mods the game will not load: shown with the reason, nothing sent."""
    return [{'name': s['mod']['name'], 'title': s['mod']['title'], 'version': s['mod']['version'],
             'strings': len(source_locale(s['mod'])[0]), 'arabic': 0, 'brand': 0, 'original': 0, 'pending': 0,
             'changed': 0, 'excluded': False, 'state': s['reason'], 'state_ar': STATES_AR[s['reason']],
             'detail': s['detail']} for s in skipped]


# ---------- the pack ----------
def build_pack(mods, arabic, owner, en, out_root=None) -> Path:
    pack = Path(out_root or DIST) / f'{PACK}_{PACK_VERSION}'
    if pack.exists():
        shutil.rmtree(pack)   # build output only
    order = {m['name']: list(source_locale(m)[0]) for m in mods}
    by_owner = {}
    for k, ar in arabic.items():
        by_owner.setdefault(owner[k], {})[k] = visual_value(k, ar)
    for name, values in by_owner.items():
        write_cfg(pack / 'locale' / 'ar' / f'{name}.cfg', values, order[name])
    major_minor = '.'.join(game_version().split('.')[:2])
    info = {'name': PACK, 'version': PACK_VERSION, 'title': 'Arabic for installed mods (generated locally)',
            'author': 'factorio-arabic', 'factorio_version': major_minor,
            'description': 'Arabic, shaped and ordered for the engine, for the other mods installed here. '
                           'Rebuilt by the Arabic mods translator; not for distribution.',
            # '? name' orders the pack after the mod. The documented dependency form has no spaces in the name, so a
            # name like 'Flow Control' is left out rather than risk the game rejecting the whole pack: its strings are
            # still translated, only a copy of Arabic that mod might ship itself would win over ours.
            'dependencies': [f'base >= {major_minor}.0', '? arabic-complete'] +
                            [f'? {n}' for n in sorted(by_owner) if DEP_NAME_RE.fullmatch(n)]}
    pack.mkdir(parents=True, exist_ok=True)
    (pack / 'info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    return pack


def lua_findings(mods, en_keys):
    """Texts no locale file can reach: hard-coded captions, and keys the code uses that no locale defines."""
    out = []
    for m in mods:
        own_sections = {k.split('/', 1)[0] for k in source_locale(m)[0]}
        for text in m['lua']:
            for kind, literal in LUA_LITERAL_RE.findall(text):
                out.append((m['name'], f'hard-coded {kind}', literal))
            for sec, key in LUA_KEY_RE.findall(text):
                if sec in own_sections and f'{sec}/{key}' not in en_keys:
                    out.append((m['name'], 'key missing even in English', f'{sec}.{key}'))
    return sorted(set(out))


def fingerprint(mods):
    parts = sorted(f"{m['name']}@{m['version']}" for m in mods) + ['keep:' + ','.join(sorted(excluded()))]
    ov = overrides_path()
    if ov.exists():
        parts.append(_sha(ov.read_text(encoding='utf-8')))
    return _sha('|'.join(parts))


# ---------- savings ----------
def savings(rows, history):
    """Measured: tokens per machine-translated string over every run with API use; what the memory hits saved."""
    machine = sum(r.get('translated', 0) for r in history)
    tokens = sum(r.get('input_tokens', 0) + r.get('output_tokens', 0) for r in history)
    per_string = tokens / machine if machine else 0
    u = rows['usage']
    glossary_tokens = round(u['input_tokens'] * u['glossary_chars'] / u['chars_in']) if u['chars_in'] else 0
    hits = sum(s in ('memory', 'memory-base') for s in rows['source'].values())
    return {'tokens_per_string': round(per_string, 1), 'memory_hits': hits,
            'tokens_saved_estimate': round(hits * per_string), 'glossary_tokens_this_run': glossary_tokens}


def report(mods, rows, findings, provider, states, last, skipped=()):
    kinds = ['override', 'mod-arabic', 'memory-base', 'memory', 'machine', 'brand', 'original', 'english']
    names = {'override': 'يدوي', 'mod-arabic': 'عربية المود', 'memory-base': 'ذاكرة اللعبة', 'memory': 'الذاكرة المشتركة',
             'original': 'أصلي (باختيارك)',
             'machine': 'ترجمة آلية جديدة', 'brand': 'اسم/اختصار', 'english': 'بالإنجليزية'}
    counts = {}
    for k, src in rows['source'].items():
        counts.setdefault(rows['owner'][k], {}).setdefault(src, 0)
        counts[rows['owner'][k]][src] += 1
    lines = [f'# ترجمة المودات الإضافية — {time.strftime("%Y-%m-%d %H:%M")}', '', f'المترجم: {provider}', '',
             '| المود | الحالة | ' + ' | '.join(names[k] for k in kinds) + ' |', '|---|---|' + '---|' * len(kinds)]
    st = {s['name']: s for s in states}
    for m in mods:
        c = counts.get(m['name'], {})
        lines.append(f"| {m['name']} {m['version']} | {st[m['name']]['state_ar']} | "
                     + ' | '.join(str(c.get(k, 0)) for k in kinds) + ' |')
    if skipped:
        lines += ['', '## مودات لن تحمّلها اللعبة (لم يُرسل منها شيء)', '', '| المود | السبب |', '|---|---|']
        lines += [f"| {s['name']} {s['version']} | {s['state_ar']}{': ' + s['detail'] if s['detail'] else ''} |"
                  for s in skipped]
    if rows.get('lang'):
        by = {}
        for k, l in rows['lang'].items():
            by[(rows['owner'][k], l)] = by.get((rows['owner'][k], l), 0) + 1
        lines += ['', '## نصوص لا إنجليزية لها في المود: مصدرها لغة أخرى فيه', '']
        lines += [f'- `{n}`: {c} نصاً من `{l}`' for (n, l), c in sorted(by.items())]
    if rows.get('paused'):
        lines += ['', '> أوقفتَ الترجمة مؤقتاً. ما تُرجم محفوظ ومثبّت، و«متابعة الترجمة» تُكمل الباقي فقط.']
    elif rows.get('stopped'):
        lines += ['', '> توقّفت الترجمة عند حدّ المزوّد (زحام أو حدّ مجاني). ما تُرجم محفوظ في الذاكرة، والتشغيل التالي '
                      'يُكمل من حيث توقّف.']
    lines += ['', '## الاستهلاك والتوفير', '',
              f"- طلبات API في هذا التشغيل: **{last['requests']}** (توكن داخل {last['input_tokens']}، خارج {last['output_tokens']})",
              f"- نصوص من الذاكرة بلا طلب: **{last['memory_hits']}**؛ توفير مقدّر ≈ {last['tokens_saved_estimate']} توكن "
              f"({last['tokens_per_string']} توكن للنص، مقيس من الطلبات الفعلية)",
              f"- حصة المسرد من التوكن الداخل في هذا التشغيل ≈ {last['glossary_tokens_this_run']}: المسرد يوحّد المصطلحات "
              'لكنه يضيف توكن إلى كل طلب، ولا يغني عن ترجمة الجملة كاملة.']
    left = sorted(k for k, s in rows['source'].items() if s == 'english')
    if left:
        lines += ['', '## ما زال بالإنجليزية', ''] + [f'- `{rows["owner"][k]}` `{k}`: {rows["en"][k][:80]}' for k in left]
    if rows.get('review'):
        lines += ['', '## مأخوذ من الذاكرة لسياق آخر (للمراجعة: قد يختلف التذكير والعدد)', '']
        lines += [f'- `{rows["owner"][k]}` `{k}` ← من `{ctx}`' for k, ctx in rows['review'][:200]]
    if rows.get('flags'):
        lines += ['', '## تنبيهات الجودة', ''] + [f'- `{rows["owner"][k]}` `{k}`: {f}' for k, f in rows['flags'][:200]]
    if rows['conflicts']:
        lines += ['', '## المفتاح نفسه في أكثر من مود (يفوز آخر مود يُحمَّل)', '']
        lines += [f'- `{k}`: {a} ← {b}' for k, a, b in rows['conflicts']]
    if findings:
        lines += ['', '## نصوص لا تصلها ملفات اللغة', ''] + [f'- `{n}` {kind}: `{t}`' for n, kind, t in findings]
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'modpack.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


# ---------- runs ----------
def _translator(offline, log):
    key = os.environ.get('FA_TRANSLATE_KEY', '')
    if offline or not key:
        return None, 'none (offline)'
    saved = _load_json(STATE / 'translator.json', {})
    tag = 'v2|' + _sha(key)[:12] + '|' + '|'.join(os.environ.get(v, '') for v in   # v2: configs carry fallbacks
                                                  ('FA_TRANSLATE_PROVIDER', 'FA_TRANSLATE_BASE_URL', 'FA_TRANSLATE_MODEL'))
    cfg = saved.get('config') if saved.get('tag') == tag else None
    if not cfg:
        cfg = translator.detect(key)   # raises TranslatorError: the caller reports it
        _save_json(STATE / 'translator.json', {'tag': tag, 'config': cfg})
    label = f"{cfg['provider']} / {cfg['model']}"
    log(f'translator: {label}')
    run = lambda batch, terms, lang='en': translator.translate(cfg, key, batch, terms, source_lang=lang)
    run.cfg = cfg   # a fallback model may take over during the run: build() reports the one that ended it
    return run, label


def _context(offline=True, log=print):
    usable, skipped = scan_mods(mods_dir(), _game_major_minor())
    mods = load_order(usable)
    mem = memory.TranslationMemory(STATE / 'memory.json')
    legacy = STATE / 'cache.json'   # first format, keyed by locale key: carried over once, never deleted
    if legacy.exists() and not (STATE / 'memory.json').exists():
        n = mem.import_legacy_cache(_load_json(legacy, {}), merge(mods)[0])
        log(f'imported {n} strings from the old cache')
    base = memory.base_memory(mods_dir())
    return mods, mem, base, skipped


def run_mark():
    """STATE/run.json while a build runs: still there at the next start means the last run was cut off (window
    closed, crash, power loss). Each answered batch is already in the memory, so running again resumes: what was
    translated comes back with no request and only the rest is sent."""
    return STATE / 'run.json'


def end_run():
    run_mark().unlink(missing_ok=True)   # our own marker: a clean end (success, or an error already reported)


def _stop_requested():
    """The window's «إيقاف مؤقت»: it creates FA_STOP_FILE; the build stops after the batch in flight, then packs."""
    p = os.environ.get('FA_STOP_FILE')
    return bool(p) and Path(p).exists()


def build(offline=False, log=print):
    progress('scan', 0, 1)
    STATE.mkdir(parents=True, exist_ok=True)
    _save_json(run_mark(), {'started_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'pid': os.getpid(), 'offline': offline})
    mods, mem, base, skipped = _context(log=log)
    terms = memory.term_base(_load_json(ROOT / 'glossary.json', {}), memory.base_terms(mods_dir()))
    translate, provider = _translator(offline, log)
    keep = excluded()
    arabic, owner, rows = resolve(mods, base=base, memory_=mem, overrides=_load_json(overrides_path(), {}),
                                  terms=terms, translate=translate, model=provider, log=log, keep=keep,
                                  should_stop=_stop_requested)
    mem.save()
    if translate:
        provider = f"{translate.cfg['provider']} / {translate.cfg['model']}"
    progress('pack', 0, 1)
    pack = build_pack(mods, arabic, owner, rows['en'])
    manifest = _load_json(STATE / 'manifest.json', {})
    for m in mods:
        if m['name'] in keep:
            continue   # kept original: no record, so switching it back shows it as new until the next build
        manifest[m['name']] = {'version': m['version'], 'fp': mod_fingerprint(m), 'built_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                               'keys': {k: _sha(rows['en'][k]) for k, o in owner.items() if o == m['name']}}
    _save_json(STATE / 'manifest.json', manifest)
    states = mod_states(mods, rows, manifest, keep)   # after this build: translated, pending, or original
    u = rows['usage']
    translated = len({memory.norm(rows['en'][k]).lower() for k, s in rows['source'].items() if s == 'machine'})  # sent
    history = (_load_json(STATE / 'usage.json', []) + [{
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'), 'provider': provider, 'translated': translated, **u}])[-100:]
    _save_json(STATE / 'usage.json', history)
    pending = sum(s == 'english' for s in rows['source'].values())
    last = {'built_at': time.strftime('%Y-%m-%dT%H:%M:%S'), 'translator': provider, 'mods': len(mods),
            'strings': len(rows['en']), 'arabic': len(arabic), 'english_left': pending, 'translated_now': translated,
            'memory_size': len(mem), 'stopped': rows['stopped'], 'paused': rows['paused'], 'pack_path': str(pack),
            **u, **savings(rows, history)}
    _save_json(STATE / 'last_run.json', last)
    report(mods, rows, lua_findings(mods, set(rows['en']) | set().union(*(read_en(m) for m in MODULES))), provider,
           states, last, skipped_states(skipped))
    _save_json(STATE / 'state.json', {'fingerprint': fingerprint(mods), 'pending': pending, 'built_at': last['built_at']})
    end_run()
    progress('done', 1, 1)
    return {'pack': pack.name, 'pack_path': str(pack), 'mods': len(mods), 'strings': len(rows['en']),
            'arabic': len(arabic), 'english_left': pending, 'requests': u['requests'], 'translator': provider,
            'error': rows['errors'][-1] if rows['errors'] else '', 'stopped': rows['stopped'], 'paused': rows['paused'],
            'skipped': len(skipped), 'built_at': last['built_at']}


def status():
    """No API call: an offline resolve tells, for each mod, what is already covered; then the mods the game will
    not load, with the reason. unlisted: mods copied in since the game last ran (it enables them on its next start)."""
    mods, mem, base, skipped = _context()
    keep = excluded()
    _, _, rows = resolve(mods, base=base, memory_=mem, overrides=_load_json(overrides_path(), {}), terms={},
                         log=lambda s: None, keep=keep)
    saved = _load_json(STATE / 'state.json', {})
    fp = fingerprint(mods)
    last = _load_json(STATE / 'last_run.json', {})
    return {'fingerprint': fp, 'changed': fp != saved.get('fingerprint'), 'pending': saved.get('pending', 0),
            'interrupted': _load_json(run_mark(), None),   # {started_at, pid, offline}: the window resumes it
            'stopped': bool(last.get('stopped')), 'paused': bool(last.get('paused')),
            'english_left': last.get('english_left', 0),
            'mods': len(mods), 'skipped': len(skipped),
            'unlisted': sum(not m.get('listed', True) for m in mods + [s['mod'] for s in skipped]),
            'states': mod_states(mods, rows, _load_json(STATE / 'manifest.json', {}), keep) + skipped_states(skipped)}


def keep_original(name: str, keep: bool) -> dict:
    """The window's checkbox. Switching back to Arabic drops the mod's build record (it shows as new) and costs no
    request for strings already in the memory; the pack changes on the next build."""
    names = set_excluded(name, keep)
    if not keep:
        manifest = _load_json(STATE / 'manifest.json', {})
        if manifest.pop(name, None) is not None:
            _save_json(STATE / 'manifest.json', manifest)
    return {'mod': name, 'original': keep, 'kept_original': names}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'build':
        try:
            print(json.dumps(build(offline='--offline' in sys.argv, log=lambda s: print(s, file=sys.stderr)),
                             ensure_ascii=False))
        except translator.TranslatorError as e:
            end_run()   # reported to the player (a refused key, say): not a cut-off run to resume on every start
            sys.exit(f'translator: {e}')
    elif cmd == 'status':
        print(json.dumps(status(), ensure_ascii=False))
    elif cmd == 'summary':
        print(json.dumps(_load_json(STATE / 'last_run.json', {}), ensure_ascii=False))
    elif cmd == 'export-tmx' and len(sys.argv) > 2:
        mem = memory.TranslationMemory(STATE / 'memory.json')
        Path(sys.argv[2]).write_text(mem.to_tmx(), encoding='utf-8')
        print(json.dumps({'tmx': sys.argv[2], 'units': len(mem)}))
    elif cmd in ('original', 'arabic') and len(sys.argv) > 2:
        print(json.dumps(keep_original(sys.argv[2], cmd == 'original'), ensure_ascii=False))
    else:
        sys.exit('usage: python -E -m tools.modpack build [--offline] | status | summary | export-tmx <file.tmx> | '
                 'original <mod> | arabic <mod>')
