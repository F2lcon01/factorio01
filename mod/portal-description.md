## العربية

![العربية في اللعبة: قبل المود وبعده]({{img:1-before-after}})

ترجمة عربية **كاملة** لـ Factorio 2.1 وتوسعة **عصر الفضاء**: القوائم والإعدادات، والعناصر والمباني، والتقنيات، والنصائح والحيل،
والإنجازات، والكواكب. **7,600 نص**، ومعها نصوص الدروس والسيناريوهات (691 نصاً) عبر أداة اللغة.

### لماذا هذا المود؟

محرك اللعبة لا يعرف تشكيل الحروف العربية ولا الكتابة من اليمين إلى اليسار، فتظهر الترجمة العربية الموجودة في اللعبة
بحروف منفصلة، وكثير من نصوصها بالإنجليزية. هذا المود يقدّم النص جاهزاً للمحرك.

| | الترجمة الحالية في اللعبة | مع هذا المود |
|---|:-:|:-:|
| الحروف | منفصلة | **متصلة** |
| الأوصاف الطويلة | ترتيب الأسطر مقلوب | **من الأعلى إلى الأسفل** |
| نصوص تظهر بالإنجليزية | 2,410 | **0** |
| نصوص فيها رموز مكسورة أو أسطر معكوسة أو مصطلحات غير موحّدة | 392 | **مصحّحة** |
| الدروس والسيناريوهات | منفصلة | **مصلحة بالأداة** |

### التثبيت

1. من داخل اللعبة: **Mods ← Install ←** ابحث عن `arabic-complete` **← Install**.
2. **Settings ← Interface ← Language ← العربية**.
3. يُنصح بأداة اللغة (أدناه): تصلح اسم «العربية» في قائمة اللغات ونصوص الدروس.

### أداة اللغة (مؤقتة حتى تصدر ترجمة عربية رسمية)

![أداة اللغة: متطابقة، أو زر إصلاح]({{img:5-language-tool}})

نافذة بسيطة فيها زر **العربية** وزر **English**، وتعرض إصدار اللعبة وإصدار المود: **«متطابقة»** أو زر **«إصلاح»**.
تصلح أيضاً اسم «العربية» في قائمة اللغات ونصوص الدروس والسيناريوهات (التي لا يصل إليها أي مود).
الموقع لا يسمح بملفات تشغيل داخل المود، لذلك تُنزَّل الأداة من GitHub، وتأخذ نصوص الدروس من المود نفسه.

**تنزيل الأداة:** [arabic-tools.zip](https://github.com/F2lcon01/factorio01/raw/main/download/arabic-tools.zip)
(أو من [صفحة الإصدارات](https://github.com/F2lcon01/factorio01/releases/latest))

1. ثبّت هذا المود، ثم **أغلق اللعبة**.
2. نزّل **arabic-tools.zip**، ثم انقر عليه بالزر الأيمن ← **«استخراج الكل»**.
3. افتح المجلد وانقر مرتين على **`Change-Language.cmd`**. إن ظهرت «Windows protected your PC» فاضغط
   **«مزيد من المعلومات» ← «تشغيل على أي حال»**، ثم **«نعم»** لصلاحيات المسؤول.
4. اختر **العربية** أو **English**، وإن ظهر **«إصلاح»** فاضغطه. ثم افتح اللعبة.

بعد كل تحديث للعبة شغّل الأداة مرة أخرى. تحفظ نسخة احتياطية قبل أي تغيير.

- **رقم الإصدار ظاهر:** يظهر رقم الأداة في شريط العنوان، وتسأل الأداة GitHub وهذا الموقع عن آخر إصدار للأداة والمود، فتعرض
  «✓ بآخر إصدار» أو «⬆ أحدث: …» رابطاً لصفحة التنزيل.
- **شاشة «خطأ في تحميل التعديلات»** تظهر حين يتعطّل مود آخر، وتظهر فيها العربية مقلوبة. السبب أنها تظهر قبل تحميل أي مود،
  فتقرأ عربية اللعبة الأصلية المقلوبة. **مود العربية لم يتعطّل.** زر «إصلاح» يجعل هذه الشاشة عربية سليمة أيضاً.

### ترجمة المودات الإضافية (أي مود تضيفه)

![أداة ترجمة المودات الإضافية]({{img:6-mods-translator}})

المودات التي تضيفها تظهر نصوصها بالإنجليزية. **أداة ترجمة المودات** تولّد على جهازك مود ترجمة محلياً
(`arabic-mods-local`) بحروف متصلة كبقية اللعبة، بمفتاح API من **أي مزوّد** (OpenAI، Gemini، Claude، DeepL، OpenRouter،
Groq، DeepSeek، Mistral، xAI). كل نص يُترجم يُحفظ في **ذاكرة مشتركة**: المود الذي لم يتغيّر لا يكلّف أي طلب، والمود
الذي تحدّث تُترجم نصوصه الجديدة فقط (قياس: التشغيل الأول طلبان، والثاني 0). ومود تريده **بلغته الأصلية** أزل
العلامة بجانبه: تبقى بقية المودات عربية، وتعود ترجماته من الذاكرة دون أي طلب متى أعدت العلامة.

**تنزيل:** [arabic-mods-translator.zip](https://github.com/F2lcon01/factorio01/releases/latest/download/arabic-mods-translator.zip)
(نحو 12 ميغا، فيه Python مدمج) ← «استخراج الكل» ← `Translate-Mods.cmd` ← الصق المفتاح ← «ترجمة وتثبيت».

- **مفتاح مجاني:** زر «احصل على مفتاح مجاني» يفتح صفحة المفاتيح في Google AI Studio (Gemini مختار مسبقاً)، أو في
  OpenRouter. مع OpenRouter لا تستعمل الأداة إلا نماذجه المجانية فقط. والنموذج المزدحم يُستبدل ببديل تلقائياً.
- **ترى كل مود في مجلد `mods`**، حتى ما نسخته قبل أن تشغّل اللعبة. المود الذي لن تحمّله اللعبة لا يُرسل منه شيء، ويظهر
  سببه: «لا يعمل مع إصدار لعبتك»، أو «ينقصه: flib»، أو «معطّل».
- **مود بلا إنجليزية** (بعض المودات تشحن البرتغالية وحدها مثلاً) تُترجم نصوصه من لغته، بدل أن تظهر «Unknown key».
- **عند حدّ المزوّد** تتوقف الأداة وتحفظ ما تُرجم، وتُكمل في التشغيل التالي من حيث توقفت.
- **إيقاف مؤقت ومتابعة:** يتوقف بعد الدفعة الجارية ويثبّت ما تُرجم. **وإن أُغلقت الأداة فجأة** (أو انقطعت الكهرباء)
  تُكمل وحدها حين تفتحها، ولا تعيد ما تُرجم.

### ما الذي في الترجمة

- الوحدات الست: `core` و`base` و`space-age` و`quality` و`elevated-rails` و`recycler`. التوسعات اختيارية: يعمل المود باللعبة الأساسية وحدها.
- مسرد موحّد من 1,055 مصطلحاً. الكواكب: نوفيس، فولكانوس، فولغورا، غليبا، أكويلو.
- صيغ الجمع العربية (مفرد، مثنى، جمع)، والأرقام لاتينية 0-9 دائماً.
- فُحص داخل محرك اللعبة نفسه: لا نص بالإنجليزية، ولا نص بلا تشكيل.

### التوافق

- Factorio **2.1**، ورقم إصدار المود يطابق رقم إصدار اللعبة.
- لا يغيّر بيانات اللعبة (checksum = 0).
- **غير متوافق** مع `zzz-arabic-shaper` (يؤدي الوظيفة نفسها).

**حدود لا يستطيع أي مود تجاوزها:** النص محاذى لليسار؛ البحث بالعربي داخل اللعبة لا يطابق الأسماء؛ نص الدردشة.

**الكود والمشاكل والاقتراحات:** [GitHub](https://github.com/F2lcon01/factorio01) ·
[أبلغ عن مشكلة](https://github.com/F2lcon01/factorio01/issues). الأسئلة الشائعة في تبويب **FAQ**.

## English

A **complete** Arabic translation of Factorio 2.1 and the **Space Age** expansion: menus and settings, items and
buildings, technologies, tips and tricks, achievements and planets. **7,600 strings**, plus the tutorial and scenario
texts (691 strings) through the language tool. The first image at the top of this page compares the two.

### Why this mod?

Factorio's text engine has no Arabic shaping and no right-to-left (bidi) support. Arabic letters change shape depending
on their neighbours, and the engine draws every letter in its isolated form, so the Arabic translation that ships with
the game shows disconnected letters, and many of its strings are still in English. This mod gives the engine text that
is already shaped and ordered, so it displays correctly.

| | Arabic shipped with the game | With this mod |
|---|:-:|:-:|
| Letters | disconnected | **connected** |
| Long descriptions | line order reversed | **top to bottom** |
| Strings still in English | 2,410 | **0** |
| Strings with broken tokens, reversed lines or inconsistent terms | 392 | **fixed** |
| Tutorials and scenarios | disconnected | **fixed by the language tool** |

### How it works

- **Pre-shaped text.** Every string is converted to Arabic presentation forms (the connected letter shapes) and
  reversed line by line, so the engine's left-to-right drawing shows it in the right reading order.
- **Pre-wrapped long descriptions.** The engine's own line wrapping reverses line order for this text, so long
  descriptions are wrapped in advance, measured in pixels against the game's tooltip width, and read top to bottom.
- **Checked inside the game engine** with the game's own locale dump: no English left, no unshaped text.

### Installation

1. In the game: **Mods → Install →** search for `arabic-complete` **→ Install**.
2. **Settings → Interface → Language → العربية**.
3. Recommended: the language tool below, which fixes the language name "العربية" in the language list and the
   tutorial texts.

### Language tool (temporary, until an official Arabic release)

A small Windows window with an **العربية** button and an **English** button. It shows the game version and the mod
version, then either **"matching"** or a **Fix** button. Fix repairs the language name in the language list and the
tutorial/scenario texts (which no mod can reach), enables the mod if it is disabled, and tells you when a newer
release of this mod exists. The mod portal does not allow scripts inside a mod, so the tool is downloaded from GitHub;
it reads the patched tutorial texts from this mod, so they always match the installed mod version.

**Download:** [arabic-tools.zip](https://github.com/F2lcon01/factorio01/raw/main/download/arabic-tools.zip)
(or from the [releases page](https://github.com/F2lcon01/factorio01/releases/latest), with SHA256 checksums)

1. Install this mod, then **close the game**.
2. Download **arabic-tools.zip**, right-click it → **Extract All**.
3. Open the folder and double-click **`Change-Language.cmd`**. If "Windows protected your PC" appears, choose
   **More info → Run anyway**, then **Yes** for administrator rights.
4. Choose **العربية** or **English**; if **Fix** appears, press it. Then start the game.

Run the tool again after every game update. It backs up every file before changing it.

- **Version shown:** the tool's version is in the title bar. The tool asks GitHub and this portal for the newest tool and mod releases, and shows "✓ up to date" or "⬆ newer: …" as a link to the download page.
- **The "Error loading mods" screen** appears when another mod fails, and its Arabic looks reversed. That screen comes before any mod is loaded, so it uses the game's own reversed Arabic. **The Arabic mod is not broken.** Fix makes that screen readable too.

### Translator for your other mods

Mods you add show their texts in English. The **mods translator** (Windows) builds a local locale mod,
`arabic-mods-local`, shaped and ordered like the rest of the game, with an API key from **any provider** (OpenAI,
Gemini, Claude, DeepL, OpenRouter, Groq, DeepSeek, Mistral, xAI). Every translated string goes into a **shared
translation memory**: an unchanged mod costs no request, and an updated mod only sends its new or changed strings
(measured: first run 2 requests, second run 0). Untick a mod to keep it in its **original language** while the others
stay Arabic; tick it again and its translations come back from the memory with no request. Each answer is checked for
placeholders, tags and plural forms before it is used.

**Download:** [arabic-mods-translator.zip](https://github.com/F2lcon01/factorio01/releases/latest/download/arabic-mods-translator.zip)
(about 12 MB, embedded Python, nothing to install) → Extract All → `Translate-Mods.cmd` → paste the key → Translate.

- **Free key:** *Get a free key* opens the key page of Google AI Studio (Gemini is preselected) or OpenRouter. With OpenRouter, the tool uses free models only. A busy model hands over to a fallback on its own.
- **Every mod in the `mods` folder is seen**, including mods copied in before the game has run. Mods the game will not load send nothing and show the reason: another game version, a missing required mod (for example flib), or disabled.
- **Mods without English:** some mods ship only Portuguese, for example. Their texts are translated from that language instead of showing "Unknown key".
- **At the provider's limit** the run stops and keeps what it translated. The next run continues from there.
- **Pause and Continue:** a pause stops the run after the batch in flight and installs what is done. If the tool is closed suddenly, or the power goes off, it continues on its own the next time you open it, and nothing translated is sent again.

### What is translated

- All six modules: `core`, `base`, `space-age`, `quality`, `elevated-rails` and `recycler`. The expansions are
  optional: the mod works with the base game alone.
- A unified glossary of 1,055 terms. Planets: نوفيس (Nauvis), فولكانوس (Vulcanus), فولغورا (Fulgora),
  غليبا (Gleba), أكويلو (Aquilo).
- Arabic plural forms (singular, dual, plural), and Western digits 0-9 throughout.

### Compatibility

- Factorio **2.1**; the mod version follows the game version.
- Does not change game data (checksum 0).
- **Incompatible** with `zzz-arabic-shaper` (same purpose).

**Limits no mod can lift:** text stays left-aligned; in-game search does not match Arabic input; chat text.

**Source, releases and bug reports:** [GitHub](https://github.com/F2lcon01/factorio01) ·
[report an issue](https://github.com/F2lcon01/factorio01/issues). More answers in the **FAQ** tab.

---
Factorio's original text © Wube Software. Builds on the community Arabic translation from Factorio's Crowdin project; this mod's processing and new/corrected strings are MIT-licensed.
