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

A **complete** Arabic locale for Factorio 2.1 and **Space Age** (7,600 strings), plus the tutorial and scenario texts (691 strings) through the language tool.

- **Connected letters, right-to-left reading order.** The engine has no Arabic shaping or bidi support, so this mod ships the text pre-shaped (Arabic presentation forms) and pre-ordered.
- **Long descriptions are pre-wrapped** so they read top-to-bottom (the engine's own wrapping reverses line order for RTL text).
- Fills **2,410** strings missing from the official Arabic translation and fixes **392** (broken tokens, reversed lines, inconsistent terms). Unified glossary of 1,055 terms; Arabic plural forms.
- Checked inside the game engine: no English left, no unshaped text.

**Enable:** Settings → Interface → Language → العربية.

**Arabic / English switcher (temporary, Windows):** shows the game and mod versions, "matching" or a one-click Fix, and patches the scenario/tutorial texts that no mod can reach. The portal does not allow scripts inside a mod, so the tool is downloaded from GitHub: [arabic-tools.zip](https://github.com/F2lcon01/factorio01/raw/main/download/arabic-tools.zip); it reads the patched texts from this mod.

**Compatibility:** Factorio 2.1; mod version = game version; does not change game data (checksum 0); expansions optional. **Incompatible** with `zzz-arabic-shaper` (same purpose).

**Limits no mod can lift:** text stays left-aligned; in-game search does not match Arabic input; chat text.

Source, releases and issues: [github.com/F2lcon01/factorio01](https://github.com/F2lcon01/factorio01).

---
Factorio's original text © Wube Software. Builds on the community Arabic translation from Factorio's Crowdin project; this mod's processing and new/corrected strings are MIT-licensed.
