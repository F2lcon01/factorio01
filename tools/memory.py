"""Translation memory shared by every mod (tools.modpack) and the term base sent with each request.
- TranslationMemory: STATE/memory.json {sha1(normalized English): {"en", "ar", "src", "model", "ts"}}. A string
  translated once, in any mod, is reused in every other mod without an API call: exact match, then case-insensitive.
- base_memory(): the base game's strings, English → Arabic: from src/ar in the project, or on a player's machine from
  the installed arabic-complete mod (un-shaped). No game text is shipped.
- base_terms() + term_base(): single words and short names (water → ماء) to keep terminology consistent; only the
  terms that occur in a batch are sent (they add tokens to every request; they never replace a sentence)."""
import hashlib, json, os, re, time, unicodedata, zipfile
from pathlib import Path
from tools.cfg import parse_cfg, read_cfg
from tools.paths import MODULES, SRC, read_en
from tools.textfx import from_visual

BIDI_RE = re.compile('[‎‏‪-‮⁦-⁩]')
NAME_SECTIONS = ['item-name', 'fluid-name', 'entity-name', 'equipment-name', 'tile-name', 'space-location-name',
                 'quality-name', 'virtual-signal-name', 'recipe-name', 'technology-name', 'item-group-name']  # priority
TERM_RE = re.compile(r"^[A-Za-z][A-Za-z'\- ]*$")


def norm(en: str) -> str:
    return re.sub(r'\s+', ' ', en).strip()


def _id(en: str) -> str:
    return hashlib.sha1(norm(en).encode('utf-8')).hexdigest()


class TranslationMemory:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.entries = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}
        self._lower = {norm(e['en']).lower(): i for i, e in self.entries.items()}

    def __len__(self):
        return len(self.entries)

    def get(self, en: str):
        e = self.entries.get(_id(en))
        if e is None:
            i = self._lower.get(norm(en).lower())
            e = self.entries.get(i) if i else None
        return e['ar'] if e else None

    def put(self, en: str, ar: str, src: str, model: str = ''):
        if not norm(en):
            return
        i = _id(en)
        self.entries[i] = {'en': norm(en), 'ar': ar, 'src': src, 'model': model,
                           'ts': time.strftime('%Y-%m-%dT%H:%M:%S')}
        self._lower[norm(en).lower()] = i

    def save(self):
        """Atomic: a crash while writing leaves the previous file intact."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.entries, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')
        os.replace(tmp, self.path)

    def import_legacy_cache(self, cache: dict, en_by_key: dict) -> int:
        """The first modpack cache was keyed by locale key with sha1(raw English): carry valid entries over."""
        n = 0
        for key, c in cache.items():
            en = en_by_key.get(key)
            if en and c.get('en') == hashlib.sha1(en.encode('utf-8')).hexdigest() and self.get(en) is None:
                self.put(en, c['ar'], c.get('src', 'machine'))
                n += 1
        return n


def unshape(visual: str) -> str:
    """Our built (shaped, line-reversed) text → normal text: NFKC folds presentation forms, reversal is an involution."""
    return from_visual(BIDI_RE.sub('', unicodedata.normalize('NFKC', visual)))


def _installed_arabic(mods_dir: Path) -> dict:
    """Locale of the newest installed arabic-complete (folder or zip) → {key: visual text}."""
    found = []
    for p in Path(mods_dir).glob('arabic-complete_*'):
        m = re.search(r'_(\d+)\.(\d+)\.(\d+)(?:\.zip)?$', p.name)
        if m:
            found.append((tuple(map(int, m.groups())), p))
    if not found:
        return {}
    path = max(found)[1]
    out = {}
    if path.is_dir():
        for f in (path / 'locale' / 'ar').glob('*.cfg'):
            out.update(read_cfg(f))
    else:
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if re.fullmatch(r'[^/]+/locale/ar/[^/]+\.cfg', n):
                    out.update(parse_cfg(z.read(n).decode('utf-8-sig')))
    return out


def _base_pairs(mods_dir, sections=None):
    """Yield (section/key, English, Arabic logical) for the base game."""
    if SRC.exists():
        for m in MODULES:
            p = SRC / f'{m}.cfg'
            ar = read_cfg(p) if p.exists() else {}
            for k, e in read_en(m).items():
                if k in ar and (sections is None or k.split('/', 1)[0] in sections):
                    yield k, e, ar[k]
        return
    vis = _installed_arabic(mods_dir) if mods_dir else {}
    for m in MODULES:
        for k, e in read_en(m).items():
            if k in vis and (sections is None or k.split('/', 1)[0] in sections):
                yield k, e, unshape(vis[k])


def base_memory(mods_dir=None) -> dict:
    out = {}
    for _, e, ar in _base_pairs(mods_dir):
        out.setdefault(norm(e).lower(), ar)
    return out


def base_terms(mods_dir=None) -> dict:
    """Names of the base game's items, buildings, fluids, technologies... (up to 3 words): water → ماء."""
    best = {}   # term → (section priority, Arabic): an item's name beats a technology of the same name
    for k, e, ar in _base_pairs(mods_dir, set(NAME_SECTIONS)):
        t, rank = norm(e).lower(), NAME_SECTIONS.index(k.split('/', 1)[0])
        if TERM_RE.match(t) and len(t.split()) <= 3 and (t not in best or rank < best[t][0]):
            best[t] = (rank, ar)
    return {t: ar for t, (_, ar) in best.items()}


def term_base(glossary: dict, names: dict) -> dict:
    """Curated glossary first (it wins), then base-game names."""
    tb = {norm(k).lower(): v for k, v in names.items()}
    tb.update({norm(k).lower(): v for k, v in glossary.items()})
    return tb


def terms_for(texts, tb: dict, limit: int = 60) -> dict:
    low = ' '.join(texts).lower()
    hits = {t: a for t, a in tb.items() if len(t) > 2 and re.search(rf'(?<![a-z]){re.escape(t)}(?![a-z])', low)}
    return dict(sorted(hits.items(), key=lambda x: (-len(x[0]), x[0]))[:limit])
