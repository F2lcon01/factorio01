## أسئلة شائعة

**فعّلت المود والحروف ما زالت منفصلة؟**
تأكد أن المود مفعّل في **Mods**، وأن اللغة **العربية** مختارة في **Settings ← Interface ← Language**، ثم أعد تشغيل اللعبة.

**اسم «العربية» في قائمة اللغات غير مقروء؟**
هذا الاسم في ملفات اللعبة نفسها ولا يصل إليه أي مود. شغّل أداة اللغة واضغط **«إصلاح»**.

**نصوص الدروس ومقدمة اللعب الحر بحروف منفصلة؟**
هذه النصوص داخل ملفات السيناريوهات ولا يصل إليها أي مود. أداة اللغة تصلحها من الملفات المصلحة داخل هذا المود.

**بعد تحديث اللعبة، هل يتوقف المود؟**
لا. اللعبة تعطّل المود فقط إذا تغيّر الرقمان الأولان (مثلاً 2.1 ← 2.2). لكن Steam قد يعيد ملفات الدروس الأصلية بعد التحديث:
شغّل الأداة واضغط **«إصلاح»** إن ظهر.

**كيف أرجع إلى الإنجليزية؟**
من الأداة: زر **English**. أو من **Settings ← Interface ← Language ← English**.

**Windows يحذّرني عند تشغيل الأداة؟**
الأداة غير موقّعة رقمياً. اضغط **«مزيد من المعلومات» ← «تشغيل على أي حال»**. كودها مفتوح على
[GitHub](https://github.com/F2lcon01/factorio01) ومعه بصمات الملفات (`SHA256SUMS.txt`) في صفحة الإصدارات.

**هل يعمل على Linux أو macOS؟**
المود نعم. أداة اللغة لويندوز فقط؛ على غيره فعّل العربية من الإعدادات.

**هل يؤثر على ملفات الحفظ؟**
لا. المود لا يغيّر بيانات اللعبة (checksum = 0)، والأداة لا تلمس ملفات الحفظ.

**ظهرت «Couldn't get Steam auth ticket» في قائمة المودات؟**
ليست من هذا المود. أغلق Steam كلياً وأعد فتحه.

## FAQ (English)

**Letters still look disconnected?** Make sure the mod is enabled and the language is set to العربية, then restart the game.

**The language name "العربية" in the language list is unreadable / tutorial texts are disconnected?** Those live in the game's own files that no mod can reach. Run the language tool (Windows) and press Fix.

**Does a game update break the mod?** No; the game only disables it when the major.minor version changes. Steam may restore the original tutorial files after an update: run the tool again.

**Windows SmartScreen warning?** The tool is not code-signed. Choose "More info" → "Run anyway". Its source and SHA256 checksums are on [GitHub](https://github.com/F2lcon01/factorio01).
