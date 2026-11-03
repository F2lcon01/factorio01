## العربية

ترجمة عربية **كاملة** لـ Factorio 2.1 وتوسعة **عصر الفضاء**: الواجهة، والعناصر، والتقنيات، والنصائح والحيل، والإنجازات — كل النصوص (7,600 نص).

- **حروف متصلة واتجاه قراءة صحيح.** محرك اللعبة لا يشكّل الحروف العربية ولا يعرف الكتابة من اليمين لليسار، فيقدّم هذا المود النص مُشكَّلاً ومرتباً مسبقاً.
- **الأوصاف الطويلة مقسّمة مسبقاً** لتُقرأ من الأعلى إلى الأسفل (التقسيم التلقائي في اللعبة يقلب ترتيب الأسطر).
- يكمل **2,410** نصاً ناقصاً في الترجمة الرسمية ويصحح **392** نصاً (رموز مكسورة، أسطر معكوسة، مصطلحات غير موحّدة).

**التفعيل:** الإعدادات ← الواجهة ← اللغة ← العربية.

### أداة اللغة (مؤقتة حتى تصدر ترجمة عربية رسمية)

داخل المود مجلد اسمه **`arabic-tools`**: نافذة بسيطة فيها زر **العربية** وزر **English**، وتفحص إصدار اللعبة
وإصدار المود: تظهر **«متطابقة»** أو زر **«إصلاح»**. تصلح أيضاً اسم «العربية» في قائمة اللغات ونصوص الدروس
والسيناريوهات (التي لا يصل إليها أي مود).

1. أغلق اللعبة.
2. اضغط **Windows + R** واكتب `%APPDATA%\Factorio\mods` ثم **Enter**.
3. افتح ملف `arabic-complete_….zip` وانسخ المجلد **`arabic-tools`** إلى سطح المكتب.
4. افتح المجلد وانقر مرتين على **`Change-Language.cmd`** ثم اضغط **«نعم»** لصلاحيات المسؤول.
5. اختر **العربية** أو **English**، وإن ظهر **«إصلاح»** فاضغطه. ثم افتح اللعبة.

الشرح الكامل خطوة بخطوة في `arabic-tools/README-AR.txt`. تحفظ الأداة نسخة احتياطية قبل أي تغيير.

**حدود لا يستطيع أي مود تجاوزها:** النص محاذى لليسار؛ البحث بالعربي داخل اللعبة لا يطابق الأسماء.

لا يغيّر بيانات اللعبة (checksum = 0). **غير متوافق** مع `zzz-arabic-shaper` (يؤدي الوظيفة نفسها).

## English

A **complete** Arabic locale for Factorio 2.1 and **Space Age** — every string of the base game and the expansion (7,600 strings).

- **Connected letters, right-to-left reading order.** The engine has no Arabic shaping or bidi support, so this mod ships the text pre-shaped (Arabic presentation forms) and pre-ordered.
- **Long descriptions are pre-wrapped** so they read top-to-bottom (the engine's own wrapping reverses line order for RTL text).
- Fills **2,410** strings missing from the official Arabic translation and fixes **392** (broken tokens, reversed lines, inconsistent terms).

**Enable:** Settings → Interface → Language → العربية.

**Limits no mod can lift:** text stays left-aligned; in-game search does not match Arabic input; scenario and tutorial texts live inside the scenario files and keep the official translation.

Does not change game data (checksum 0). **Incompatible** with `zzz-arabic-shaper` (same purpose).

---
Factorio's original text © Wube Software. Builds on the community Arabic translation from Factorio's Crowdin project; this mod's processing and new/corrected strings are MIT-licensed.
