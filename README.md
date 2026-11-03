<div align="center">

![Factorio Arabic](https://capsule-render.vercel.app/api?type=waving&color=0:1a1a1a,50:5a3a10,100:ff9c00&height=200&section=header&text=Factorio%20Arabic&fontSize=48&fontColor=ffffff&fontAlignY=35&desc=Complete%20Arabic%20%C2%B7%20connected%20letters%20%C2%B7%20right-to-left&descAlignY=58&descAlign=50)

[![Version](https://img.shields.io/badge/🔖_version-2.1.24-ff9c00?style=for-the-badge)](https://mods.factorio.com/mod/arabic-complete)
[![Factorio](https://img.shields.io/badge/🏭_Factorio-2.1_%2B_Space_Age-c47800?style=for-the-badge)](https://factorio.com)
[![Strings](https://img.shields.io/badge/🔤_strings-7600-5a3a10?style=for-the-badge)](#-الملخص)
[![Tests](https://img.shields.io/badge/🛡️_tests-51_passing-22c55e?style=for-the-badge)](tests)
[![F2lcon01](https://img.shields.io/badge/👤_F2lcon01-GitHub-1e3a5f?style=for-the-badge&logo=github&logoColor=white)](https://github.com/F2lcon01)

**تعريب كامل للعبة Factorio وتوسعة عصر الفضاء، بحروف متصلة واتجاه قراءة صحيح.**

<br>

[![Download the tool](https://img.shields.io/badge/⬇_Download-arabic--tools.zip-ff9c00?style=for-the-badge)](https://github.com/F2lcon01/factorio01/raw/main/download/arabic-tools.zip)
[![Mod portal](https://img.shields.io/badge/🧩_Mod_portal-arabic--complete-5a3a10?style=for-the-badge)](https://mods.factorio.com/mod/arabic-complete)

</div>

---

## 📋 الفهرس

| # | القسم | المحتوى |
|:-:|---|---|
| 1 | [🎮 للاعبين](#-للاعبين) | التثبيت خطوة بخطوة، وأداة اللغة وزر «إصلاح» |
| 2 | [🏆 لماذا هذا المود](#-لماذا-هذا-المود) | الفرق عن الترجمة العربية الحالية في اللعبة |
| 3 | [🔬 كيف يعمل](#-كيف-يعمل) | لماذا الحروف متصلة والأسطر مرتبة |
| 4 | [🔧 للمطورين](#-للمطورين) | خط الإنتاج والنشر والتحديث والاسترجاع |
| 5 | [📏 الحدود](#-الحدود) | ما لا يستطيع أي مود تغييره |
| 6 | [📈 الملخص](#-الملخص) | الأرقام |

---

## 🎮 للاعبين

> [!NOTE]
> **أداة اللغة مؤقتة**: إلى أن تصدر شركة Wube ترجمة عربية رسمية تعرض الحروف متصلة.
> موقع المودات لا يسمح بملفات تشغيل داخل أي مود، لذلك تُنزَّل الأداة من هنا. أما نصوص الدروس المصلحة
> فهي داخل المود، والأداة تأخذها منه، فتبقى مطابقة لإصدار المود دائماً.

### ▶️ التثبيت خطوة بخطوة

1️⃣ **ثبّت المود** من داخل اللعبة: **Mods ← Install ←** ابحث عن `arabic-complete` **← Install**، ثم **أغلق اللعبة**.

2️⃣ **نزّل الأداة**: [arabic-tools.zip](https://github.com/F2lcon01/factorio01/raw/main/download/arabic-tools.zip)،
ثم انقر عليها بالزر الأيمن ← **«استخراج الكل» (Extract All)**.

3️⃣ **شغّلها**: افتح المجلد وانقر مرتين على **`Change-Language.cmd`**.
إن ظهرت رسالة زرقاء «Windows protected your PC» فاضغط **«مزيد من المعلومات» ← «تشغيل على أي حال»**،
ثم **«نعم»** لصلاحيات المسؤول.

4️⃣ **اختر** **العربية** أو **English**. إن ظهر زر **«إصلاح»** فاضغطه. ثم افتح اللعبة.

<div align="center">

![أداة اللغة: على اليسار متطابقة، وعلى اليمين المود أقدم من اللعبة فيظهر زر إصلاح](docs/images/tool-states.png)

*على اليسار: كل شيء متطابق. على اليمين: المود أقدم من اللعبة، فيظهر زر «إصلاح».*

</div>

### 🔄 ماذا يفعل زر «إصلاح»

| المشكلة | ما تفعله الأداة |
|---|---|
| 🟡 إصدار المود لا يطابق إصدار اللعبة | تسأل موقع المودات: إن وُجد إصدار أحدث تفتح صفحته لتحدّثه من **Mods ← Updates**؛ وإلا تخبرك أن المود يعمل |
| 🔴 المود غير متوافق (مثلاً لعبة 2.2) | تخبرك بانتظار تحديث المود |
| 🔴 المود غير مثبت | ترشدك إلى **Mods ← Install** وتفتح صفحة المود |
| 🟡 المود معطّل | تفعّله |
| 🟡 اسم «العربية» مقطّع في قائمة اللغات | تصلحه |
| 🟡 Steam أعاد نصوص الدروس الأصلية بعد تحديث | تعيد ترقيعها، بعد حفظ الأصل احتياطياً |

> [!TIP]
> **بعد كل تحديث للعبة** شغّل الأداة مرة أخرى. لا تحتاج إلى تنزيلها من جديد.
> النسخ الاحتياطية في `%APPDATA%\Factorio\arabic-tools-backup`.

<details>
<summary><b>❓ أسئلة شائعة</b></summary>

| السؤال | الجواب |
|---|---|
| ظهرت «أغلق اللعبة أولاً» | أغلق Factorio تماماً ثم أعد المحاولة. اللعبة تحفظ إعداداتها عند الإغلاق |
| هل تغيّر الأداة شيئاً في حفظ ألعابي؟ | لا. تغيّر فقط لغة اللعبة، وملفات نصوص الدروس، واسم اللغة |
| كيف أرجع كل شيء كما كان؟ | اضغط «English»، ثم من Steam: كليك يمين على Factorio ← خصائص ← الملفات المثبتة ← التحقق من سلامة ملفات اللعبة |
| بلا الأداة؟ | الإعدادات ← الواجهة ← اللغة ← **العربية**. يعمل المود، لكن اسم اللغة ونصوص الدروس تبقى بلا إصلاح |
| «Couldn't get Steam auth ticket» | ليست من المود. أغلق Steam كلياً وأعد فتحه |

الشرح الكامل للمبتدئين: [`mod/README-AR.txt`](mod/README-AR.txt) · تغيير اللغة بالتفصيل: [`LANGUAGE.md`](LANGUAGE.md)

</details>

---

## 🏆 لماذا هذا المود

محرك Factorio لا يعرف تشكيل الحروف العربية ولا الكتابة من اليمين لليسار، فتظهر الترجمة العربية الموجودة في اللعبة
بحروف منفصلة ومقلوبة. هذا المود يقدّم النص جاهزاً للمحرك.

| الجانب | العربية الحالية في اللعبة | هذا المود |
|---|:-:|:-:|
| **الحروف** | 🔴 منفصلة | 🟢 **متصلة** |
| **اتجاه القراءة** | 🔴 مقلوب | 🟢 **من اليمين لليسار** |
| **الأوصاف الطويلة** | 🔴 ترتيب الأسطر مقلوب | 🟢 **من الأعلى للأسفل** |
| **التغطية** | 🔴 2,410 نصاً بالإنجليزي | 🟢 **7,600 نص كلها عربية** |
| **الجودة** | 🔴 392 نصاً فيها رموز مكسورة أو أسطر معكوسة أو مصطلحات غير موحّدة | 🟢 **مصحّحة** |
| **الدروس والسيناريوهات** | 🔴 منفصلة | 🟢 **مصلحة بالأداة** |
| **بيانات اللعبة** | — | 🟢 **لا تتغيّر** (checksum = 0) |

<div align="center">

![نص عربي متصل داخل محرك اللعبة](docs/images/in-game-tooltip.png)

*لقطة من داخل محرك اللعبة: حروف متصلة، وأسطر مرتبة من الأعلى للأسفل.*

</div>

---

## 🔬 كيف يعمل

```mermaid
graph LR
    A["src/ar/*.cfg<br/>نص عربي عادي"] --> B["tools.build<br/>تشكيل + عكس + لفّ مسبق"]
    B --> C["arabic-complete.zip<br/>mods.factorio.com"]
    S["src/scenarios/**"] --> P["scenario-patch/<br/>داخل المود"]
    P --> C
    T["download/arabic-tools.zip<br/>GitHub"] --> G["Change-Language.cmd<br/>عند اللاعب"]
    C --> G
    G --> F["config.ini · اسم اللغة<br/>نصوص الدروس"]

    style B fill:#ff9c00,stroke:#c47800,color:#000
    style C fill:#5a3a10,stroke:#ff9c00,color:#fff
    style G fill:#22c55e,stroke:#15803d,color:#fff
```

| المشكلة في المحرك | الحل |
|---|---|
| لا يشكّل العربية ولا يعرف اليمين لليسار | نبني النص بأشكال العرض المتصلة (Presentation Forms) ونعكسه سطراً سطراً |
| اللفّ التلقائي يقلب ترتيب الأسطر | نلفّ مسبقاً بالبكسل (`WRAP = 460`، معايَر داخل اللعبة على عرض التلميح) |
| المود لا يصل إلى نصوص السيناريوهات (مُثبت) | `scenario-patch/` داخل المود، تطبّقها الأداة مع نسخة احتياطية |
| موقع المودات يرفض ملفات التشغيل داخل المود | الأداة على GitHub، والبيانات داخل المود |

الأدلة: `reports/spike.md`، `reports/verify-game.md`. السجل الكامل لكل قرار واكتشاف: [`docs/DEVLOG.md`](docs/DEVLOG.md).

---

## 🔧 للمطورين

`src/ar/*.cfg` و`src/scenarios/**` نص عربي **منطقي عادي** (كما يُكتب). لا تحرّر ملفات `dist/` أبداً.

<details open>
<summary><b>خط الإنتاج (بالترتيب)</b></summary>

```powershell
python -E -m tools.import_official          # الرسمي → منطقي + work/todo.jsonl
python -E -m tools.glossary --apply-decisions # توحيد المصطلحات (glossary_decisions.json)
python -E -m tools.terms apply              # أسماء النماذج المترجمة مرة واحدة
python -E -m tools.batches                  # تقسيم الباقي
python -E -m tools.merge NNN                # لكل دفعة مترجمة
python -E -m tools.corrections              # term_migrations + corrections.json + قاعدة الجمع + أرقام لاتينية + سولفيج
python -E -m tools.lint                     # يجب: errors=0
python -E -m pytest                         # كل الاختبارات
python -E -m tools.verify_game 2.1.24       # داخل المحرك: english=0 unshaped=0
python -E -m tools.visual_check 2.1.24      # لقطات شاشة حقيقية → reports/screens
python -E -m tools.build 2.1.24             # dist/arabic-complete_2.1.24
powershell -NoProfile -File tools\install.ps1 -Version 2.1.24   # تثبيت + تفعيل (نسخة احتياطية لـ mod-list.json)
python -E -m tools.scenarios build; python -E -m tools.scenarios apply   # رقعة السيناريوهات
python -E -m tools.scenario_check           # المحرك يقرأ نص السيناريو المرقّع (بلا نافذة وبلا Steam)
```

> [!IMPORTANT]
> التثبيت بـ PowerShell لا Python: نسخة Python من Microsoft Store تحوّل كتاباتها تحت `%APPDATA%`
> إلى نسخة خاصة لا تراها اللعبة (مُثبت). `tools/install.py` يرفض عمداً ويشير إلى `install.ps1`.

</details>

<details>
<summary><b>النشر</b></summary>

رقم إصدار المود = رقم إصدار اللعبة.

```powershell
python -E -m tools.package 2.1.24                                   # zip المود + Crowdin + download/arabic-tools.zip
pwsh -NoProfile -File tools\publish.ps1 -Version 2.1.24 -DryRun     # فحص محلي
pwsh -NoProfile -File tools\publish.ps1 -Version 2.1.24 -Update     # إصدار جديد؛ يطلب المفتاح بإدخال مخفي
```

- قبل كل إصدار: أضف قسماً في `mod/changelog.txt` (يفحص `tools.package` صيغته).
- الموقع يرفض أي ملف تنفيذي داخل المود (`InvalidModUpload`)، و`tools.package` و`publish.ps1` يرفضانه قبل الرفع.
- إن تغيّر `download/arabic-tools.zip` فارفعه إلى GitHub مع الإصدار.

</details>

<details>
<summary><b>بعد كل تحديث للعبة</b></summary>

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\auto_update.ps1   # يعيد البناء برقم اللعبة ويثبّت ويفحص
python -E -m tools.sync                     # مفاتيح جديدة/متغيرة → work/todo.jsonl
# ترجمة → merge → lint → pytest → verify_game → package → publish
python -E -m tools.sync --refresh-snapshot
python -E -m tools.scenarios status         # إن ظهر 'other' فالتحديث استبدل الملفات: أعد build + apply
```

التفاصيل والجدولة التلقائية: [`LANGUAGE.md`](LANGUAGE.md).

</details>

<details>
<summary><b>الاسترجاع</b></summary>

```powershell
powershell -NoProfile -File tools\install.ps1 -Uninstall   # تعطيل + نقل المود إلى %APPDATA%\Factorio\mods-parked (لا حذف)
python -E -m tools.scenarios restore     # إعادة ملفات السيناريو الأصلية بايتاً بايتاً (مُختبر على اللعبة الحقيقية)
```

أو من Steam: «التحقق من سلامة ملفات اللعبة» يعيد ملفات السيناريو الأصلية.

</details>

---

## 📏 الحدود

> [!WARNING]
> لا يستطيع أي مود تغيير هذه: محاذاة النص لليسار · البحث بالعربي داخل اللعبة · نص الدردشة.

**استثناءات موثّقة:** 8 أسماء مكتوبة حرفياً في كود اللعبة نفسها (`localised_name = "dummy"` في `trains.lua`/`enemies.lua`،
وخطأ في `explosions.lua:7885`)، وهي كيانات داخلية لا تظهر للاعب. مسجّلة في `tools/verify_game.py: EXCEPTIONS`.

---

## 📈 الملخص

<div align="center">

| النصوص | العدد | النسبة |
|---|:-:|:-:|
| 🟢 من الترجمة الرسمية كما هي (بعد التشكيل) | 4,798 | ![](https://img.shields.io/badge/63%25-22c55e?style=flat-square) |
| 🟡 مصحّحة | 392 | ![](https://img.shields.io/badge/5%25-f59e0b?style=flat-square) |
| 🟠 جديدة (كانت بالإنجليزي) | 2,410 | ![](https://img.shields.io/badge/32%25-ff9c00?style=flat-square) |
| **🔤 المجموع** | **7,600** | ![](https://img.shields.io/badge/100%25-5a3a10?style=flat-square) |

| ✅ نصوص الدروس | 📖 المسرد | 🧩 الوحدات | 🛡️ الاختبارات |
|:-:|:-:|:-:|:-:|
| 691 نصاً في 23 ملفاً | 1,055 مصطلحاً | core · base · space-age · quality · elevated-rails · recycler | 51 |

</div>

---

<div align="center">

**Factorio Arabic v2.1.24**: F2lcon01

النص الأصلي للعبة © Wube Software. يبني على الترجمة العربية المجتمعية في مشروع Factorio على Crowdin.
معالجة هذا المشروع ونصوصه الجديدة والمصحّحة بترخيص MIT، كما هو مسجّل في صفحة المود.

[![GitHub](https://img.shields.io/badge/GitHub-F2lcon01-1e3a5f?style=for-the-badge&logo=github&logoColor=white)](https://github.com/F2lcon01)

![Footer](https://capsule-render.vercel.app/api?type=waving&color=0:ff9c00,50:5a3a10,100:1a1a1a&height=100&section=footer)

</div>
