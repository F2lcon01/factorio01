# Factorio Arabic (complete + shaped) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** مود `arabic-complete` يعرّب Factorio 2.1.24 (+ Space Age) بنسبة 100% بحروف متصلة واتجاه قراءة صحيح، دون لمس ملفات اللعبة.

**Architecture:** مصدر الحقيقة نصّ عربي **منطقي عادي** قابل للتحرير (`src/ar/*.cfg`). أداة بناء تحوّله إلى الصيغة التي يفهمها المحرك: أشكال عرض متصلة (Presentation Forms) + ترتيب بصري معكوس لكل سطر + لفّ أسطر مسبق للأوصاف الطويلة. الناتج مود يُحمَّل بعد الوحدات الرسمية فيتجاوز كل مفاتيحها العربية.

**Tech Stack:** Python 3.13 · arabic-reshaper 3.0.1 · fontTools 4.68.0 · python-bidi 0.6.12 (للاختبار المقارن فقط) · pytest · `factorio.exe --dump-prototype-locale` للتحقق الآلي.

## Global Constraints

- إصدار اللعبة: `2.1.24` · `factorio_version` في المود: `"2.1"`.
- لا تعديل على `C:\Program Files (x86)\Steam\steamapps\common\Factorio\` إطلاقاً (باستثناء Task 12 الاختياري بنسخة احتياطية واسترجاع).
- لا حذف لأي ملف للمستخدم: الإلغاء = تعطيل + نقل إلى `_disabled\`.
- المصدر `src/ar/*.cfg`: UTF-8 بلا BOM، نص منطقي، **ممنوع** فيه: أشكال عرض (U+FB50–FDFF, U+FE70–FEFF)، PUA، محارف اتجاه (U+200E/F, U+202A–E, U+2066–9).
- كل رمز (`__1__`, `__CONTROL__x__`, `[item=x]`, `[font=x]`, `\n`, `__plural_for_parameter__N__{}`) يطابق الإنجليزي بايتاً بايتاً (مقارنة multiset).
- الحركات (التشكيل) تُحذف في الناتج فقط (المحرك لا يموضعها)، وتبقى مسموحة في المصدر.
- أرقام لاتينية (0-9) كما في الترجمة الرسمية.
- كل مسار تشغيل للعبة يجب أن يكون < 260 حرفاً (ثبت أن `-c` يفشل مع مسار طويل).
- Git: لا ذكر لـ AI/Claude في أي commit، لا `Co-Authored-By`، لا `git push` بلا طلب.

---

## الحكم والأدلة (لماذا هذا التصميم)

| الحقيقة | الدليل |
|---|---|
| العربية موجودة رسمياً لكن ناقصة: 5,880/8,291 مفتاح (71%)، الناقص **2,411** (core 1,647 · space-age 749 · recycler 6 · base 5 · quality 3 · wave-defense 1) | `audit.py` على `data\*\locale\{en,ar}` |
| النص الرسمي مخزّن **معكوساً بصرياً وغير متصل** | `data\base\locale\ar\base.cfg:3` → `arachnophilia=.نورترديابس ِنبا`؛ صفر محارف أشكال عرض في كل ملفات ar |
| المحرك لا يملك تشكيلاً عربياً ولا BiDi | لا توجد سلاسل `harfbuzz/fribidi/bidi` في `bin\x64\factorio.exe`؛ ومود المجتمع `zzz-arabic-shaper` موجود فقط لإصلاح «الحروف المنفصلة» |
| الخط جاهز: لا حاجة لمود خطوط | `NotoSansArabic` Regular/Bold/SemiBold تغطي **140/140** محرفاً مطلوباً (منها 125 شكل عرض)، وهو أول خط في سلسلة `data\core\locale\en\info.json` يغطيها |
| المود **يتجاوز** النص الرسمي (مثبت) | تجربة `--dump-prototype-locale` بمود اختباري: `iron-plate` و`vulcanus` ظهرا بنصّنا المتصل، و`copper-plate` بقي رسمياً |
| مود الترجمة لا يمس حالة اللعبة | سجل التجربة: `Checksum of arabic-spike: 0` |
| الترجمة الرسمية فيها عيوب يجب إصلاحها | 147 رموز مكسورة (مثل `__رصانعلا-رايتخا__CONTROL__`)، 92 مكتوبة بالاتجاه الخطأ، 49 مطابقة للإنجليزي، 37 بلا عربي، جمع مكسور `{1=تارييغت=يقابلا\|رييغت}`، 379 فيها حركات |
| محوّلنا موثوق | نموذج `textfx.py`: انعكاس ذاتي 5,768/5,880 (الفشل = العيوب أعلاه)، وتطابق 4,971/5,001 مع python-bidi (الفروق: `20٪` عندنا أصح من `٪20`) |

### القرار: مود مستقل (موصى به) مقابل البدائل

| المسار | يصمد أمام تحديث Steam | يصلح الاتصال | يكمل الناقص | الاسترجاع |
|---|---|---|---|---|
| **مود `arabic-complete`** ✅ | نعم | نعم | نعم | تعطيل المود |
| تعديل ملفات اللعبة مباشرة | لا (يُمسح عند التحديث/التحقق) | نعم | نعم | نسخة احتياطية |
| `zzz-arabic-shaper` الموجود | نعم | نعم (للـ 71% فقط) | لا | — مصمَّم لـ 2.0 ولا يصلح الرموز المكسورة |
| Crowdin الرسمي فقط | نعم | **لا** (المحرك لا يشكّل) | نعم | — |

Crowdin يبقى مخرجاً ثانوياً (Task 11): نفس المصدر يُصدَّر بالصيغة الرسمية غير المتصلة لمن يريد المساهمة.

### حدود لا يمكن إصلاحها بمود (تُذكر للمستخدم بصراحة)

- محاذاة النص يسار دائماً (المحرك لا يعرف المحاذاة لليمين).
- البحث داخل اللعبة بالعربي لا يطابق (المكتوب حروف عادية والأسماء أشكال عرض).
- اسم اللغة في قائمة اختيار اللغات يأتي من `core\locale\ar\info.json` (غير متصل).
- ما يكتبه اللاعبون في الدردشة لا يُشكَّل.

---

## File Structure

```
factorio-arabic/
  requirements.txt              # pinned deps
  pytest.ini
  tools/__init__.py
  tools/paths.py                # GAME_DATA, ROOT, SRC, WORK, DIST, REPORTS
  tools/cfg.py                  # read/write .cfg in English key order
  tools/textfx.py               # logical -> visual (shape + reverse + wrap)
  tools/lint.py                 # per-value and per-module validation
  tools/import_official.py      # official visual ar -> src logical + todo/defects
  tools/glossary.py             # en->ar term pairs from existing names
  tools/batches.py              # split todo into translation batches
  tools/merge.py                # validate + merge translated batches into src
  tools/build.py                # src -> dist/arabic-complete_<ver>/
  tools/verify_game.py          # headless dump check in isolated env
  tools/install.py              # install/enable + uninstall/disable (no delete)
  tools/sync.py                 # after game update: new/changed en keys
  mod/info.json                 # template
  mod/changelog.txt
  src/ar/<module>.cfg           # SOURCE OF TRUTH (logical Arabic)
  src/en_snapshot.json          # sha1 of each en value at translation time
  glossary.json
  work/todo.jsonl  work/batches/NNN.jsonl  work/out/NNN.jsonl
  reports/defects.md  reports/review-NNN.md  reports/screens/
  dist/arabic-complete_<ver>/
  tests/conftest.py tests/test_cfg.py tests/test_textfx.py tests/test_lint.py tests/test_build.py
```

---

## Phase 0 — بوابة التحقق البصري (تُنفَّذ بعد Task 2 وقبل أي ترجمة)

### Task 0: تجربة داخل اللعبة لأربعة أسئلة مفتوحة

ما ثبت آلياً: التجاوز للأسماء والأوصاف. ما **لم** يثبت بعد ويُحسم هنا بالعين:
(1) الحروف متصلة فعلاً على الشاشة، (2) مفاتيح واجهة `core` (غير النماذج) تُتجاوز أيضاً، (3) نصوص السيناريو (`freeplay`) تُتجاوز أم لا، (4) عرض اللفّ المناسب `WRAP`.

**Files:**
- Create: `tools/spike_build.py` → يكتب `%TEMP%\fa-spike\mods\arabic-spike_0.0.2\locale\ar\spike.cfg` و`info.json`

**Interfaces:**
- Consumes: `to_visual` من Task 2 (لذلك يأتي ترتيبه بعد Task 2).

- [ ] **Step 1: ابنِ مود التجربة** (بيئة معزولة قصيرة المسار، لا تمس إعدادات المستخدم)

```python
"""Spike mod: python -E -m tools.spike_build"""
import json, os
from pathlib import Path
from tools.textfx import to_visual

env = Path(os.environ['TEMP']) / 'fa-spike'
mod = env / 'mods' / 'arabic-spike_0.0.2'
(mod / 'locale' / 'ar').mkdir(parents=True, exist_ok=True)
long_desc = ('هذا وصف طويل للاختبار يحتوي على كلمات كثيرة حتى نعرف أين يقطع المحرك السطر '
             'ونختار العرض المناسب للف الأسطر قبل البناء النهائي للمود العربي الكامل')
lines = [
    # root key (freeplay.cfg has msg-intro outside any section) must precede every [section]
    'msg-intro=' + to_visual('مرحباً بك في اللعب الحر. هذا نص اختبار للسيناريو.'),
    '[gui-menu]', 'single-player-menu=' + to_visual('لعب فردي'),
    '[item-name]', 'iron-plate=' + to_visual('صفيحة حديد'),
    '[item-description]',
    'iron-plate=' + to_visual(long_desc, wrap=40),
    'copper-plate=' + to_visual(long_desc, wrap=60),
    'steel-plate=' + to_visual(long_desc, wrap=80),
    'iron-gear-wheel=' + to_visual(long_desc),
]
(mod / 'locale' / 'ar' / 'spike.cfg').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(mod / 'info.json').write_text(json.dumps({
    'name': 'arabic-spike', 'version': '0.0.2', 'title': 'spike', 'author': 'Falcon',
    'factorio_version': '2.1', 'dependencies': ['base >= 2.1.0', '? space-age >= 2.1.0']}), encoding='utf-8')
print(mod)
```

- [ ] **Step 2: أبعد النسخة القديمة** `arabic-spike_0.0.1` من `%TEMP%\fa-spike\mods\` إلى `%TEMP%\fa-spike\old\` (وجود إصدارين لنفس المود يربك الاختيار). `mod-list.json` لا يتغير لأن الاسم ثابت.

- [ ] **Step 3: شغّل اللعبة بواجهتها** على البيئة المعزولة:

```powershell
$t = "$env:TEMP\fa-spike"
Start-Process 'C:\Program Files (x86)\Steam\steamapps\common\Factorio\bin\x64\factorio.exe' -ArgumentList "-c $t\config\config.ini --mod-directory $t\mods"
```

- [ ] **Step 4: افحص وصوّر** (Falcon أو أداة التحكم بالشاشة بإذن) واحفظ في `reports/screens/spike-*.png`:

| # | الشاشة | المتوقع | إن فشل |
|---|---|---|---|
| 1 | القائمة الرئيسية → زر «لعب فردي» | متصل ومقروء | المحرك يتجاوز core؟ لا → Task 12 لـ core |
| 2 | تلميح صفيحة الحديد/النحاس/الفولاذ/الترس | الأسطر تُقرأ من الأعلى للأسفل بالترتيب | اختر أصغر WRAP لا ينكسر فيه السطر تلقائياً |
| 3 | لعبة حرة جديدة → رسالة البداية | نص الاختبار | يبقى الرسمي → Task 12 للسيناريوهات |
| 4 | الحروف عموماً | متصلة، بلا مربعات فارغة | **توقف** وأعد التخطيط (مشكلة خط) |

- [ ] **Step 5: سجّل القرار** في `reports/spike.md`: قيمة `WRAP` النهائية، وهل Task 12 مطلوب (core/سيناريو).

**بوابة:** لا يبدأ Phase 2 قبل نجاح البند 4.

---

## Phase 1 — الأدوات

### Task 1: الهيكل + قراءة/كتابة ملفات cfg

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `tools/__init__.py`, `tools/paths.py`, `tools/cfg.py`, `tests/conftest.py`, `tests/test_cfg.py`

**Interfaces:**
- Produces: `read_cfg(path) -> dict[str, str]` بمفاتيح `"section/key"` (الجذر = `"/key"`)، `write_cfg(path, values, order) -> None`، `read_en(module) -> dict` (مخزّنة)، ثوابت `GAME_DATA, ROOT, SRC, WORK, DIST, REPORTS, MODULES`.

- [ ] **Step 1: الملفات الأساسية**

`requirements.txt`:
```
arabic-reshaper==3.0.1
python-bidi==0.6.12
fonttools==4.68.0
pytest>=8
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = .
```

`tools/paths.py`:
```python
import os
from functools import lru_cache
from pathlib import Path

GAME_DATA = Path(os.environ.get('FACTORIO_DATA', r'C:\Program Files (x86)\Steam\steamapps\common\Factorio\data'))
GAME_EXE = GAME_DATA.parent / 'bin' / 'x64' / 'factorio.exe'
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'ar'
WORK = ROOT / 'work'
DIST = ROOT / 'dist'
REPORTS = ROOT / 'reports'
MODULES = ['core', 'base', 'elevated-rails', 'quality', 'recycler', 'space-age']


@lru_cache(maxsize=None)
def read_en(module: str) -> dict[str, str]:
    from tools.cfg import read_cfg
    return read_cfg(GAME_DATA / module / 'locale' / 'en' / f'{module}.cfg')
```

- [ ] **Step 2: الاختبار الفاشل** `tests/test_cfg.py`:

```python
from tools.cfg import read_cfg, write_cfg
from tools.paths import GAME_DATA


def test_reads_sections_and_root_keys(tmp_path):
    p = tmp_path / 'a.cfg'
    p.write_text('root=R\n; comment\n[item-name]\niron-plate=Iron plate\n', encoding='utf-8')
    assert read_cfg(p) == {'/root': 'R', 'item-name/iron-plate': 'Iron plate'}


def test_write_follows_given_order_and_skips_missing(tmp_path):
    p = tmp_path / 'b.cfg'
    write_cfg(p, {'s/b': '2', 's/a': '1'}, ['s/a', 's/x', 's/b'])
    assert p.read_text(encoding='utf-8') == '[s]\na=1\nb=2\n'


def test_roundtrip_every_official_locale_file(tmp_path):
    files = list(GAME_DATA.glob('**/locale/en/*.cfg')) + list(GAME_DATA.glob('**/locale/ar/*.cfg'))
    assert files
    for i, src in enumerate(files):
        vals = read_cfg(src)
        out = tmp_path / f'{i}.cfg'
        write_cfg(out, vals, list(vals))
        assert read_cfg(out) == vals, src
```

- [ ] **Step 3: شغّل** `python -E -m pytest tests/test_cfg.py -v` — المتوقع: FAIL (`ModuleNotFoundError: tools.cfg`).

- [ ] **Step 4: التنفيذ** `tools/cfg.py`:

```python
"""Read/write Factorio .cfg locale files; keys are 'section/key' ('' section = root)."""
import re
from pathlib import Path

SECTION_RE = re.compile(r'^\[([^\]]+)\]\s*$')


def read_cfg(path) -> dict[str, str]:
    out, sec = {}, ''
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line or line[0] in ';#':
            continue
        m = SECTION_RE.match(line)
        if m:
            sec = m.group(1)
        elif '=' in line:
            k, v = line.split('=', 1)
            out[f'{sec}/{k}'] = v
    return out


def write_cfg(path, values: dict[str, str], order: list[str]) -> None:
    lines, sec = [], None
    for full in order:
        if full not in values:
            continue
        s, k = full.split('/', 1)
        if s != sec:
            if s:
                lines.append(f'[{s}]')
            sec = s
        lines.append(f'{k}={values[full]}')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
```

- [ ] **Step 5: شغّل** نفس الأمر — المتوقع: 3 passed.
- [ ] **Step 6: Commit** — `git init` ثم `git add -A && git commit -m "feat: cfg reader/writer with English key order"`

### Task 2: محوّل النص (القلب)

**Files:**
- Create: `tools/textfx.py`, `tests/test_textfx.py`

**Interfaces:**
- Produces: `to_visual(logical, *, shape=True, wrap=None) -> str`، `from_visual(visual) -> str`، `wrap_logical(text, width) -> str`، ثوابت `NL='\\n'`, `INLINE_RE`, `FORMAT_RE`.

- [ ] **Step 1: الاختبار الفاشل** `tests/test_textfx.py`:

```python
from tools.cfg import read_cfg
from tools.paths import GAME_DATA
from tools.textfx import NL, from_visual, to_visual, wrap_logical


def test_sentence_reversed_period_moves_left_digits_kept():
    assert to_visual('بناء 100 جهاز.', shape=False) == '.زاهج 100 ءانب'


def test_parameter_token_atomic():
    assert to_visual('عامل متغير __1__', shape=False) == '__1__ ريغتم لماع'


def test_control_icon_tokens_atomic_and_brackets_mirrored():
    s = 'اضغط __CONTROL__build__ لوضع [item=iron-plate] (الأحمر).'
    assert to_visual(s, shape=False) == '.(رمحألا) [item=iron-plate] عضول __CONTROL__build__ طغضا'


def test_format_tags_stay_in_place_per_segment():
    s = '[font=heading-2]تهانينا![/font][font=default]\\nلقد وصلت.[/font]'
    assert to_visual(s, shape=False) == '[font=heading-2]!انيناهت[/font][font=default]\\n.تلصو دقل[/font]'


def test_plural_forms_reversed_inside_block():
    s = 'لديك __plural_for_parameter__1__{1=عنصر|rest=عناصر}__'
    assert to_visual(s, shape=False) == '__plural_for_parameter__1__{1=رصنع|rest=رصانع}__ كيدل'


def test_shaping_lam_alef_ligature():
    assert to_visual('لا') == '\uFEFB'


def test_harakat_removed_in_output():
    assert to_visual('العَرَبِيَّة') == to_visual('العربية')


def test_involution_unshaped():
    s = 'اضغط __CONTROL__build__ لوضع [item=iron-plate] (الأحمر).'
    assert from_visual(to_visual(s, shape=False)) == s


def test_wrap_keeps_logical_line_order():
    out = to_visual('واحد اثنان ثلاثة أربعة خمسة', shape=False, wrap=12)
    assert [from_visual(l) for l in out.split(NL)] == ['واحد اثنان', 'ثلاثة أربعة', 'خمسة']


def test_wrap_never_splits_tokens():
    s = 'خذ __plural_for_parameter__1__{1=عنصر واحد|rest=عناصر}__ الآن'
    for line in wrap_logical(s, 5).split(NL):
        assert line.count('{') == line.count('}')


def test_involution_rate_on_official_arabic():
    vals = [v for p in GAME_DATA.glob('**/locale/ar/*.cfg') for v in read_cfg(p).values()]
    ok = sum(to_visual(from_visual(v), shape=False) == v for v in vals)
    assert ok / len(vals) >= 0.98  # measured 5768/5880 on 2.1.24; failures = known defects
```

- [ ] **Step 2: شغّل** `python -E -m pytest tests/test_textfx.py -v` — المتوقع: FAIL (import).

- [ ] **Step 3: التنفيذ** `tools/textfx.py` (هذا هو النموذج المُختبَر على بيانات اللعبة الحقيقية):

```python
"""Logical Arabic -> Factorio visual text (presentation forms, reversed per line)."""
import re
import arabic_reshaper

NL = '\\n'  # literal backslash-n as stored in .cfg files
HARAKAT_RE = re.compile(r'[\u064B-\u065F\u0670]')
FORMAT_RE = re.compile(r'\[/?(?:font|color)(?:=[^\]]*)?\]|__(?:CONTROL_STYLE|REMARK_COLOR)_(?:BEGIN|END)__')
FORMAT_SPLIT = re.compile(f'({FORMAT_RE.pattern})')
PLURAL_RE = re.compile(r'(__plural_for_parameter__\d+__\{)([^}]*)(\}__)')
INLINE = (r'__plural_for_parameter__\d+__\{[^}]*\}__'
          r'|__[A-Z][A-Z_]*__(?:\d+__)?(?:[a-z0-9][a-z0-9\-]*__)?'
          r'|__\d+__'
          r'|\[[a-z\-]+=[^\]]*\]')
INLINE_RE = re.compile(INLINE)
LTR = r"[A-Za-z0-9](?:[A-Za-z0-9 .,:/%+\-_'×]*[A-Za-z0-9%])?"
UNIT_RE = re.compile(f'{INLINE}|{LTR}|.', re.S)
MIRROR = dict(zip('()[]{}<>«»', ')(][}{><»«'))
_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True})


def _unit(u):
    m = PLURAL_RE.fullmatch(u)
    if m:
        forms = [f.partition('=') for f in m.group(2).split('|')]
        return m.group(1) + '|'.join(f'{c}={_reverse_run(t)}' if eq else _reverse_run(c)
                                     for c, eq, t in forms) + m.group(3)
    return MIRROR.get(u, u)


def _reverse_run(text):
    return ''.join(_unit(u) for u in reversed(UNIT_RE.findall(text)))


def _visible_len(text):
    return len(INLINE_RE.sub('xx', FORMAT_RE.sub('', text)))


def wrap_logical(text, width):
    """Hard-wrap logical text at word boundaries; tokens never split."""
    out = []
    for para in text.split(NL):
        words, line = re.findall(f'(?:{INLINE}|\\S)+', para), ''
        for w in words:
            cand = f'{line} {w}' if line else w
            if line and _visible_len(cand) > width:
                out.append(line)
                line = w
            else:
                line = cand
        out.append(line)
    return NL.join(out)


def to_visual(logical, *, shape=True, wrap=None):
    text = wrap_logical(logical, wrap) if wrap and _visible_len(logical) > wrap else logical
    lines = []
    for line in text.split(NL):
        if shape:
            line = _RESHAPER.reshape(HARAKAT_RE.sub('', line))
        parts = FORMAT_SPLIT.split(line)
        lines.append(''.join(p if FORMAT_RE.fullmatch(p) else _reverse_run(p) for p in parts))
    return NL.join(lines)


def from_visual(visual):
    """Inverse of to_visual(shape=False): reversal is an involution."""
    return to_visual(visual, shape=False)
```

- [ ] **Step 4: شغّل** — المتوقع: 11 passed.
- [ ] **Step 5: Commit** — `git commit -am "feat: logical-to-visual Arabic converter for Factorio"`

### Task 3: الفاحص (lint)

**Files:**
- Create: `tools/lint.py`, `tests/test_lint.py`, `lint_allow.txt` (مفاتيح مسموح أن تبقى بلا عربي، مفتاح لكل سطر)

**Interfaces:**
- Consumes: `read_cfg`, `read_en`, `MODULES`, `SRC`.
- Produces: `signature(s) -> Counter`، `check_value(en, ar, allow_latin=False) -> list[str]` (أسماء أخطاء: `tokens|plural|forbidden-char|no-arabic`)، `lint_module(module) -> tuple[list[str], list[str]]` (errors, warnings)، CLI: `python -E -m tools.lint` يخرج 1 عند وجود أخطاء.

- [ ] **Step 1: الاختبار الفاشل** `tests/test_lint.py`:

```python
from tools.lint import check_value


def test_ok():
    assert check_value('Press __CONTROL__build__.', 'اضغط __CONTROL__build__.') == []


def test_token_changed():
    assert 'tokens' in check_value('Press __CONTROL__build__.', 'اضغط __CONTROL__بناء__.')


def test_newline_count_must_match():
    assert 'tokens' in check_value('a\\nb', 'أ ب')


def test_plural_without_condition():
    en = '__1__ __plural_for_parameter__1__{1=change|rest=changes}__'
    assert 'plural' in check_value(en, '__1__ __plural_for_parameter__1__{1=تغيير|تغييرات}__')


def test_presentation_forms_forbidden_in_source():
    assert 'forbidden-char' in check_value('Plate', 'ﺻﻔﻴﺤﺔ')


def test_untranslated_latin():
    assert 'no-arabic' in check_value('Iron plate', 'Iron plate')
    assert check_value('Iron plate', 'Iron plate', allow_latin=True) == []
```

- [ ] **Step 2: شغّل** `python -E -m pytest tests/test_lint.py -v` — FAIL.

- [ ] **Step 3: التنفيذ** `tools/lint.py`:

```python
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


def signature(s):
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
```

- [ ] **Step 4: شغّل** — المتوقع: 6 passed.
- [ ] **Step 5: Commit** — `git commit -am "feat: locale lint (tokens, plurals, forbidden chars, staleness)"`

---

## Phase 2 — الاستيراد والمصطلحات والترجمة

### Task 4: استيراد الترجمة الرسمية + تقرير العيوب + المسرد

**Files:**
- Create: `tools/import_official.py`, `tools/glossary.py`
- Produces data: `src/ar/<module>.cfg`, `src/en_snapshot.json`, `work/todo.jsonl`, `reports/defects.md`, `glossary.json`

**Interfaces:**
- Consumes: `read_cfg, write_cfg, read_en, from_visual, to_visual, check_value, MODULES`.
- Produces: سطر `work/todo.jsonl` = `{"module","key","en","hint","reason"}` حيث `reason ∈ {missing, tokens, plural, no-arabic, direction, not-involutive}`.

- [ ] **Step 1: التنفيذ** `tools/import_official.py`:

```python
"""Official visual ar -> logical src; everything defective or missing goes to todo."""
import hashlib, json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import check_value
from tools.paths import GAME_DATA, MODULES, REPORTS, ROOT, SRC, WORK, read_en
from tools.textfx import from_visual, to_visual


def classify(en, vis):
    logical = from_visual(vis)
    if to_visual(logical, shape=False) != vis:
        return logical, 'not-involutive'
    if en.rstrip().endswith('.') and vis.rstrip().endswith('.') and not vis.lstrip().startswith('.'):
        return logical, 'direction'
    errs = check_value(en, logical)
    return logical, (errs[0] if errs else None)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    todo, snap, counts = [], {}, {}
    for m in MODULES:
        en = read_en(m)
        official = read_cfg(GAME_DATA / m / 'locale' / 'ar' / f'{m}.cfg')
        good = {}
        for k, e in en.items():
            snap[f'{m}:{k}'] = hashlib.sha1(e.encode('utf-8')).hexdigest()
            if k not in official:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'missing'})
                continue
            logical, reason = classify(e, official[k])
            if reason:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': logical, 'reason': reason})
            else:
                good[k] = logical
        write_cfg(SRC / f'{m}.cfg', good, list(en))
    for t in todo:
        counts[t['reason']] = counts.get(t['reason'], 0) + 1
    WORK.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
    (WORK / 'todo.jsonl').write_text('\n'.join(json.dumps(t, ensure_ascii=False) for t in todo) + '\n', encoding='utf-8')
    (ROOT / 'src' / 'en_snapshot.json').write_text(json.dumps(snap, indent=0), encoding='utf-8')
    rows = '\n'.join(f'| {r} | {n} |' for r, n in sorted(counts.items(), key=lambda x: -x[1]))
    (REPORTS / 'defects.md').write_text(f'| reason | keys |\n|---|---|\n{rows}\n', encoding='utf-8')
    print(counts, 'todo total =', len(todo))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: شغّل** `python -E -m tools.import_official` — المتوقع (مُقاس على 2.1.24 بهذا الكود حرفياً):
  `{'missing': 2410, 'not-involutive': 81, 'direction': 81, 'tokens': 42, 'no-arabic': 36, 'forbidden-char': 1}` → `todo total = 2651`.
- [ ] **Step 3: تحقق** `python -E -m tools.lint` — المتوقع: core 1808 · base 76 · elevated-rails 2 · quality 7 · recycler 6 · space-age 752 = **2651** = طول `todo.jsonl` بالضبط (خروج 1 متوقع هنا).
- [ ] **Step 3b:** راجع الـ 36 `no-arabic`: ما كان اسماً علماً أو اختصاراً مقصوداً (مثل UPS) يُضاف مفتاحه `module:section/key` إلى `lint_allow.txt` ويُحذف من `todo.jsonl`؛ الباقي يُترجم.

- [ ] **Step 4: المسرد** `tools/glossary.py`:

```python
"""Build glossary.json {english term (lower): arabic logical} from translated prototype names."""
import json, sys
from tools.cfg import read_cfg
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


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: شغّل** `python -E -m tools.glossary` — المتوقع: `743 terms; 34 conflicts` (مثل `crude oil: نفط الخام | نفط خام`، `fire: نار | حريق`). احسم الـ 34 يدوياً في `glossary.json` (Falcon يقرر المصطلح المعتمد)، وصحّح المفاتيح المخالفة في `src/ar/*.cfg` لتوحيد المصطلح.
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: import official Arabic as logical source, defects report, glossary"`

### Task 5: الترجمة على دفعات (2,651 مفتاحاً = 2,410 ناقص + 241 معيب → 23 دفعة)

**Files:**
- Create: `tools/batches.py`, `tools/merge.py`
- Data: `work/batches/NNN.jsonl` → `work/out/NNN.jsonl` → `src/ar/*.cfg`

**Interfaces:**
- Consumes: `todo.jsonl`, `glossary.json`, `check_value`, `read_en`, `write_cfg`.
- Produces: سطر مخرَج = `{"module","key","ar"}` (نص منطقي عادي).

- [ ] **Step 1:** `tools/batches.py`:

```python
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
```

- [ ] **Step 2: ترجمة كل دفعة** بوكيل فرعي مستقل، بهذا الموجّه حرفياً (يُستبدل `NNN`):

```
Translate Factorio UI strings from English to Modern Standard Arabic.
Input: work/batches/NNN.jsonl (fields module,key,en,hint,reason) and work/batches/NNN.glossary.json.
Output: work/out/NNN.jsonl, one JSON object per input line: {"module","key","ar"}. Same count, same order.
Rules:
1. Write normal logical Arabic (as typed). Never reverse text, never use presentation forms or direction marks.
2. Copy every token byte-for-byte: __1__, __CONTROL__x__, __ALT_CONTROL__1__x__, __ITEM__x__, [item=x], [entity=x],
   [tip=x], [font=x]...[/font], [color=x]...[/color], __CONTROL_STYLE_BEGIN__/END__, and keep the exact number of \n.
3. Plurals: keep __plural_for_parameter__N__{...}__; every form is cond=text; allowed conds: numbers, "ends in N", rest.
   Arabic forms: 1=, 2=, rest= at minimum.
4. Glossary terms are mandatory (use the given Arabic exactly). Planet/brand names: transliterate consistently with glossary.
5. Style: concise game UI; imperative for actions (اضغط، ضع، اسحب); no harakat unless needed to disambiguate; Western digits.
6. If "hint" is non-empty it is a previous defective translation: reuse its wording where correct, fix the defect named in "reason".
Do not touch any other file.
```

- [ ] **Step 3:** `tools/merge.py`:

```python
"""Validate translated batch output and merge it into src/ar/<module>.cfg."""
import json, sys
from tools.cfg import read_cfg, write_cfg
from tools.lint import check_value
from tools.paths import SRC, WORK, read_en


def merge(n: str):
    rows = [json.loads(l) for l in (WORK / 'out' / f'{n}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    rejected, by_module = [], {}
    for r in rows:
        errs = check_value(read_en(r['module'])[r['key']], r['ar'])
        if errs:
            rejected.append({**r, 'errors': errs})
        else:
            by_module.setdefault(r['module'], {})[r['key']] = r['ar']
    for m, vals in by_module.items():
        cur = read_cfg(SRC / f'{m}.cfg')
        cur.update(vals)
        write_cfg(SRC / f'{m}.cfg', cur, list(read_en(m)))
    (WORK / 'out' / f'{n}.rejected.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in rejected) + '\n', encoding='utf-8')
    return len(rows) - len(rejected), len(rejected)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print('merged=%d rejected=%d' % merge(sys.argv[1]))
```

- [ ] **Step 4:** لكل دفعة: `python -E -m tools.merge NNN` — المرفوض يُعاد لنفس الوكيل مع سبب الرفض حتى `rejected=0`.
- [ ] **Step 5: مراجعة بشرية:** لكل دفعة 20 مفتاحاً عشوائياً في `reports/review-NNN.md` (جدول: المفتاح | الإنجليزي | العربي) — Falcon يقبل أو يصحح مباشرة في `src/ar/*.cfg`.
- [ ] **Step 6:** بعد آخر دفعة: `python -E -m tools.lint` — المتوقع: `errors=0` لكل الوحدات (خروج 0).
- [ ] **Step 7: Commit** بعد كل دفعة مدموجة — `git commit -am "i18n(ar): batch NNN"`

---

## Phase 3 — البناء والتحقق

### Task 6: بناء المود + اختبار تغطية الخط

**Files:**
- Create: `tools/build.py`, `mod/info.json`, `mod/changelog.txt`, `tests/test_build.py`

**Interfaces:**
- Consumes: `read_cfg, write_cfg, read_en, to_visual, MODULES, SRC, DIST, GAME_DATA`.
- Produces: `build(version: str, shape: bool = True, out_root=DIST) -> Path` (مسار مجلد المود)؛ CLI `python -E -m tools.build 1.0.0 [--crowdin]`.

- [ ] **Step 1:** `mod/info.json`:

```json
{
  "name": "arabic-complete",
  "version": "0.0.0",
  "title": "Arabic — complete & shaped",
  "author": "Falcon",
  "factorio_version": "2.1",
  "description": "Complete Arabic translation with connected letters and correct reading order.",
  "dependencies": ["base >= 2.1.0", "? elevated-rails >= 2.1.0", "? quality >= 2.1.0",
                   "? recycler >= 2.1.0", "? space-age >= 2.1.0", "! zzz-arabic-shaper"]
}
```

`mod/changelog.txt`:
```
---------------------------------------------------------------------------------------------------
Version: 1.0.0
Date: 2026-11-03
  Features:
    - Complete Arabic locale for core, base, elevated-rails, quality, recycler, space-age.
    - Connected letters (presentation forms) and right-to-left reading order.
```

- [ ] **Step 2: الاختبار الفاشل** `tests/test_build.py`:

```python
import json
from fontTools.ttLib import TTFont
from tools.build import build
from tools.cfg import read_cfg
from tools.paths import GAME_DATA, MODULES, read_en


def test_mod_structure(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    assert mod.name == 'arabic-complete_9.9.9'
    info = json.loads((mod / 'info.json').read_text(encoding='utf-8'))
    assert info['version'] == '9.9.9' and info['factorio_version'] == '2.1'
    for m in MODULES:
        assert (mod / 'locale' / 'ar' / f'{m}.cfg').exists()


def test_every_output_char_has_a_glyph(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    cmap = set()
    for f in ['NotoSansArabic-Regular', 'NotoSansArabic-Bold', 'NotoSansArabic-SemiBold',
              'TitilliumWeb-Regular', 'NotoSans-Regular', 'DejaVuSans']:
        cmap |= set(TTFont(GAME_DATA / 'core' / 'fonts' / f'{f}.ttf', lazy=True).getBestCmap())
    used = {c for p in (mod / 'locale' / 'ar').glob('*.cfg') for c in p.read_text(encoding='utf-8')}
    missing = sorted(f'U+{ord(c):04X}' for c in used if ord(c) > 0x7F and ord(c) not in cmap)
    assert missing == []


def test_output_has_no_logical_arabic_letters_left(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    for p in (mod / 'locale' / 'ar').glob('*.cfg'):
        for k, v in read_cfg(p).items():
            assert not any('\u0621' <= c <= '\u064A' for c in v), (p.name, k)


def test_key_coverage_equals_english(tmp_path):
    mod = build('9.9.9', out_root=tmp_path)
    for m in MODULES:
        assert read_cfg(mod / 'locale' / 'ar' / f'{m}.cfg').keys() == read_en(m).keys()
```

ملاحظة: `test_output_has_no_logical_arabic_letters_left` يصح لأن المشكِّل يحوّل كل حرف عربي أساسي إلى شكل عرض. إن ظهر حرف لا يملك شكل عرض (نادر)، أضِفه لقائمة استثناء صريحة داخل الاختبار مع تعليق.

- [ ] **Step 3: شغّل** `python -E -m pytest tests/test_build.py -v` — FAIL.

- [ ] **Step 4:** `tools/build.py`:

```python
"""Build dist/arabic-complete_<version>/ from src/ar (logical) -> visual shaped locale."""
import json, re, shutil, sys
from pathlib import Path
from tools.cfg import read_cfg, write_cfg
from tools.paths import DIST, MODULES, ROOT, SRC, read_en
from tools.textfx import to_visual

WRAP = 60  # chars per line; set from reports/spike.md (Task 0)
WRAP_SECTION_RE = re.compile(r'description|tips-and-tricks|story|^$')


def build(version: str, shape: bool = True, out_root: Path = DIST) -> Path:
    name = 'arabic-complete' if shape else 'arabic-crowdin'
    mod = Path(out_root) / f'{name}_{version}'
    if mod.exists():
        shutil.rmtree(mod)  # build output only, never user data
    loc = mod / 'locale' / 'ar'
    for m in MODULES:
        src = read_cfg(SRC / f'{m}.cfg')
        vis = {k: to_visual(v, shape=shape,
                            wrap=WRAP if shape and WRAP_SECTION_RE.search(k.split('/', 1)[0]) else None)
               for k, v in src.items()}
        write_cfg(loc / f'{m}.cfg', vis, list(read_en(m)))
    info = json.loads((ROOT / 'mod' / 'info.json').read_text(encoding='utf-8'))
    info['version'] = version
    (mod / 'info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    shutil.copy(ROOT / 'mod' / 'changelog.txt', mod / 'changelog.txt')
    return mod


if __name__ == '__main__':
    print(build(sys.argv[1], shape='--crowdin' not in sys.argv))
```

- [ ] **Step 5: شغّل** — المتوقع: 4 passed. ثم `python -E -m pytest` كاملاً — كله أخضر.
- [ ] **Step 6: Commit** — `git commit -am "feat: build shaped mod + font coverage tests"`

### Task 7: تحقق آلي داخل محرك اللعبة (headless)

**Files:**
- Create: `tools/verify_game.py`

**Interfaces:**
- Consumes: `build`, `read_cfg`, `GAME_EXE`, `MODULES`.
- Produces: CLI يطبع `checked=N mismatched=M` ويخرج 1 إن M>0؛ يكتب `reports/verify-game.md`.

- [ ] **Step 1:** `tools/verify_game.py` (نفس الطريقة التي نجحت في التجربة: مسار قصير + إعدادات معزولة):

```python
"""Run factorio --dump-prototype-locale in an isolated env and compare with the built mod."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
from tools.build import build
from tools.cfg import read_cfg
from tools.paths import GAME_EXE, REPORTS

ENV = Path(os.environ['TEMP']) / 'fa-verify'
USER_CFG = Path(os.environ['APPDATA']) / 'Factorio' / 'config' / 'config.ini'
BASE_MODS = ['base', 'elevated-rails', 'quality', 'recycler', 'space-age']


def prepare(version):
    if ENV.exists():
        shutil.rmtree(ENV)  # our own temp env only
    (ENV / 'config').mkdir(parents=True); (ENV / 'mods').mkdir(); (ENV / 'write').mkdir()
    cfg = USER_CFG.read_text(encoding='utf-8-sig')
    cfg = re.sub(r'(?m)^write-data=.*$', f'write-data={ENV / "write"}', cfg)
    cfg = re.sub(r'(?m)^locale=.*$', 'locale=ar', cfg)
    (ENV / 'config' / 'config.ini').write_text(cfg, encoding='utf-8')
    mod = build(version, out_root=ENV / 'mods')
    mods = [{'name': n, 'enabled': True} for n in BASE_MODS + ['arabic-complete']]
    (ENV / 'mods' / 'mod-list.json').write_text(json.dumps({'mods': mods}), encoding='utf-8')
    return mod


def main(version='0.0.1'):
    sys.stdout.reconfigure(encoding='utf-8')
    mod = prepare(version)
    subprocess.run([str(GAME_EXE), '-c', str(ENV / 'config' / 'config.ini'),
                    '--mod-directory', str(ENV / 'mods'), '--dump-prototype-locale'], check=True, timeout=600)
    built = {}
    for p in (mod / 'locale' / 'ar').glob('*.cfg'):
        built.update(read_cfg(p))
    checked, bad = 0, []
    for dump in (ENV / 'write' / 'script-output').glob('*-locale.json'):
        ptype = dump.name[:-len('-locale.json')]
        data = json.loads(dump.read_text(encoding='utf-8'))
        for kind, section in (('names', f'{ptype}-name'), ('descriptions', f'{ptype}-description')):
            for proto, got in data.get(kind, {}).items():
                exp = built.get(f'{section}/{proto}')
                if exp is None or '__' in exp:
                    continue  # not ours, or contains runtime-resolved parameters
                checked += 1
                if got != exp.replace('\\n', '\n'):
                    bad.append(f'| {section}/{proto} | {got[:60]} |')
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / 'verify-game.md').write_text(
        f'checked={checked} mismatched={len(bad)}\n\n| key | game shows |\n|---|---|\n' + '\n'.join(bad[:200]) + '\n',
        encoding='utf-8')
    print(f'checked={checked} mismatched={len(bad)}')
    sys.exit(1 if bad or checked == 0 else 0)


if __name__ == '__main__':
    main(*sys.argv[1:])
```

- [ ] **Step 2: شغّل** `python -E -m tools.verify_game` — المتوقع: `checked` بالآلاف و`mismatched=0`.
  - إن ظهر `mismatched` لأن المحرك يحوّل `\n`: صحّح المقارنة حسب ما يظهر في `reports/verify-game.md` (السطر الأول من الفروق يبيّن الشكل الفعلي) ثم أعد التشغيل.
- [ ] **Step 3: Commit** — `git commit -am "test: headless in-engine locale verification"`

### Task 8: التحقق البصري النهائي (قائمة فحص بالصور)

- [ ] **Step 1:** ابنِ وثبّت في البيئة المعزولة (`python -E -m tools.verify_game` يتركها جاهزة في `%TEMP%\fa-verify`)، ثم شغّل الواجهة:

```powershell
$t = "$env:TEMP\fa-verify"
Start-Process 'C:\Program Files (x86)\Steam\steamapps\common\Factorio\bin\x64\factorio.exe' -ArgumentList "-c $t\config\config.ini --mod-directory $t\mods"
```

- [ ] **Step 2:** صوّر كل شاشة واحفظها `reports/screens/NN-name.png` وعلّم النتيجة:

| # | الشاشة | يُفحص |
|---|---|---|
| 1 | القائمة الرئيسية + الإعدادات (كل التبويبات) | اتصال الحروف، لا `__1__` ولا `\n` حرفية |
| 2 | مولّد الخريطة (Nauvis + Vulcanus) | أسماء الموارد والإعدادات |
| 3 | شجرة التقنيات + وصف تقنية طويل | ترتيب الأسطر من الأعلى |
| 4 | Factoriopedia (عنصر، كيان، كوكب) | الأسماء والأوصاف والإحصاءات |
| 5 | تلميح عنصر بوصف طويل + أيقونات داخلية | أيقونات `[item=]` في مكانها |
| 6 | Tips & Tricks (3 بطاقات) | نصوص طويلة متعددة الأسطر |
| 7 | واجهة القطارات/الدوائر (`gui-train`, `gui-control-behavior-modes`) | أكبر الأقسام المترجمة حديثاً |
| 8 | شاشة الكواكب/المنصة الفضائية (Space Age) | المصطلحات من المسرد |
| 9 | رسالة بداية اللعب الحر | حسب نتيجة Task 0 |
| 10 | نافذة اختصارات لوحة المفاتيح (`controls`) | `__CONTROL__` مُحلّة |

- [ ] **Step 3:** كل عيب → يُصحَّح في `src/ar/*.cfg` (أو `WRAP`) ثم `pytest` + `verify_game` + إعادة الصورة. البوابة: 10/10 ✅.

---

## Phase 4 — التثبيت والصيانة

### Task 9: التثبيت والاسترجاع (بدون حذف)

**Files:**
- Create: `tools/install.py`

**Interfaces:**
- Produces: `python -E -m tools.install <version>` و`python -E -m tools.install --uninstall`.

- [ ] **Step 1:** `tools/install.py`:

```python
"""Install the built mod into the user's Factorio mods folder, or disable it (never deletes)."""
import json, os, shutil, sys, time
from pathlib import Path
from tools.paths import DIST

FACTORIO = Path(os.environ['APPDATA']) / 'Factorio'
MODS = FACTORIO / 'mods'
PARKED = FACTORIO / 'mods-parked'  # outside mods/: the game would try to load any folder inside it
LIST = MODS / 'mod-list.json'
NAME = 'arabic-complete'


def _stamp():
    return time.strftime('%Y%m%d-%H%M%S')


def _set_enabled(flag: bool):
    shutil.copy(LIST, PARKED / f'mod-list.json.bak-{_stamp()}')
    data = json.loads(LIST.read_text(encoding='utf-8-sig'))
    data['mods'] = [m for m in data['mods'] if m['name'] != NAME] + [{'name': NAME, 'enabled': flag}]
    LIST.write_text(json.dumps(data, indent=2), encoding='utf-8')


def _park_old():
    for old in MODS.glob(f'{NAME}_*'):
        shutil.move(str(old), PARKED / f'{old.name}-{_stamp()}')


def install(version):
    src = DIST / f'{NAME}_{version}'
    PARKED.mkdir(exist_ok=True)
    _park_old()
    shutil.copytree(src, MODS / src.name)
    _set_enabled(True)
    print('installed', src.name, '-> set Settings > Interface > Language = العربية')


def uninstall():
    PARKED.mkdir(exist_ok=True)
    _park_old()
    _set_enabled(False)
    print('disabled; folders parked in', PARKED)


if __name__ == '__main__':
    uninstall() if '--uninstall' in sys.argv else install(sys.argv[1])
```

- [ ] **Step 2:** `python -E -m tools.build 1.0.0` ثم `python -E -m tools.install 1.0.0` — بإذن Falcon (يكتب في `%APPDATA%\Factorio\mods`).
- [ ] **Step 3:** داخل اللعبة: Settings → Interface → Language → العربية. افتح لعبة حرة وتأكد أن المود مفعّل في قائمة المودات.
- [ ] **Step 4: Rollback مُختبَر:** `python -E -m tools.install --uninstall` ثم تأكد أن اللعبة تعود للعربية الرسمية دون أخطاء، ثم أعد التثبيت.
- [ ] **Step 5: Commit** — `git commit -am "feat: install/uninstall with backups, no deletion"`

### Task 10: المزامنة بعد تحديثات Steam

**Files:**
- Create: `tools/sync.py`

- [ ] **Step 1:** `tools/sync.py`:

```python
"""After a game update: list new/changed/removed English keys and append them to work/todo.jsonl.
--refresh-snapshot: run only after every queued key is merged; marks current English as translated."""
import hashlib, json, sys
from tools.cfg import read_cfg
from tools.paths import MODULES, ROOT, SRC, WORK, read_en


def refresh_snapshot():
    snap = {}
    for m in MODULES:
        src = read_cfg(SRC / f'{m}.cfg')
        for k, e in read_en(m).items():
            if k in src:
                snap[f'{m}:{k}'] = hashlib.sha1(e.encode('utf-8')).hexdigest()
    (ROOT / 'src' / 'en_snapshot.json').write_text(json.dumps(snap, indent=0), encoding='utf-8')
    print('snapshot keys =', len(snap))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    snap = json.loads((ROOT / 'src' / 'en_snapshot.json').read_text(encoding='utf-8'))
    todo, seen = [], set()
    for m in MODULES:
        for k, e in read_en(m).items():
            sk = f'{m}:{k}'; seen.add(sk)
            h = hashlib.sha1(e.encode('utf-8')).hexdigest()
            if sk not in snap:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'new'})
            elif snap[sk] != h:
                todo.append({'module': m, 'key': k, 'en': e, 'hint': '', 'reason': 'changed'})
    removed = sorted(set(snap) - seen)
    WORK.mkdir(exist_ok=True)
    with open(WORK / 'todo.jsonl', 'a', encoding='utf-8') as f:
        for t in todo:
            f.write(json.dumps(t, ensure_ascii=False) + '\n')
    print(f'new/changed={len(todo)} removed={len(removed)}')


if __name__ == '__main__':
    refresh_snapshot() if '--refresh-snapshot' in sys.argv else main()
```

- [ ] **Step 2:** بعد كل تحديث للعبة: `sync` → `batches` → ترجمة → `merge` → `lint` → `pytest` → `verify_game` → `build <ver+1>` → `install`.
- [ ] **Step 3:** بعد دمج كل المفاتيح المعلّقة: `python -E -m tools.sync --refresh-snapshot`، ثم `python -E -m tools.lint` — المتوقع: صفر تحذيرات `stale`.
- [ ] **Step 4: Commit.**

### Task 11 (اختياري): مخرَج Crowdin للمساهمة الرسمية

- [ ] `python -E -m tools.build 1.0.0 --crowdin` → `dist/arabic-crowdin_1.0.0/locale/ar/*.cfg` بالصيغة الرسمية (معكوس، غير متصل، بلا لفّ). المساهمة يدوية من Falcon على Crowdin بحسابه.

### Task 12 (مشروط بنتيجة Task 0): رقعة السيناريوهات/الحملات

يُنفَّذ فقط إن أثبت Task 0 أن المود لا يصل لنصوص السيناريو. النطاق: 23 مجلد `locale` تحت `data\base\scenarios|campaigns|tutorials` (مفتاح واحد ناقص فقط، لكن كلها غير متصلة).

- [ ] أداة `tools/patch_scenarios.py` بأمرين: `--apply` (نسخ احتياطي كامل إلى `backups/<timestamp>/` ثم كتابة النسخة المتصلة فوق ملفات `ar`) و`--restore` (استرجاع من آخر نسخة). يتطلب صلاحية مدير لأن المسار تحت `Program Files (x86)`، ويُعاد بعد كل تحديث/تحقق Steam.
- [ ] **موافقة Falcon الصريحة قبل أي كتابة في مجلد اللعبة.**

---

## ترتيب التنفيذ والبوابات

| المرحلة | المهام | البوابة للانتقال |
|---|---|---|
| 1 | Tasks 1–3 | `pytest` أخضر (20 اختباراً) |
| 0 | Task 0 (بعد Task 2) | الحروف متصلة على الشاشة + `WRAP` محسوم + قرار Task 12 |
| 2 | Tasks 4–5 | `lint` = 0 أخطاء، مراجعة عينات كل دفعة |
| 3 | Tasks 6–8 | `pytest` + `verify_game mismatched=0` + 10/10 صور |
| 4 | Tasks 9–10 | تثبيت + استرجاع مُختبَران |

## المخاطر

| الخطر | الأثر | المعالجة |
|---|---|---|
| مفاتيح `core` غير النماذج لا تُتجاوز | الواجهة تبقى منفصلة | يُكشف في Task 0 قبل الترجمة → Task 12 يشمل core |
| اللفّ التلقائي للمحرك يقلب ترتيب الأسطر | أوصاف تُقرأ من الأسفل | لفّ مسبق بـ `WRAP` مُعايَر بصرياً |
| جودة ترجمة آلية لـ 2,700 مفتاح | مصطلحات غير متسقة | مسرد إلزامي + `lint` + مراجعة عينات |
| تحديث Steam يضيف/يغيّر مفاتيح | نص إنجليزي أو قديم | `sync.py` + تحذير `stale` في `lint` |
| تعارض مع `zzz-arabic-shaper` | تشكيل مزدوج | `"! zzz-arabic-shaper"` في `info.json` |
| اللعب الجماعي يتطلب نفس قائمة المودات | رفض الاتصال بخادم بلا المود | غير مُختبَر — الـ checksum = 0 مؤشر جيد؛ يُختبر يدوياً عند الحاجة، والحل تعطيل المود |
