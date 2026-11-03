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

**أين أبلغ عن خطأ في الترجمة؟**
افتح بلاغاً على [GitHub](https://github.com/F2lcon01/factorio01/issues) واكتب فيه النص الإنجليزي والترجمة العربية
التي تقترحها، أو استعمل تبويب **Discussion** في هذه الصفحة.

## FAQ (English)

**I enabled the mod but the letters are still disconnected.**
Check that the mod is enabled in **Mods** and that **Settings → Interface → Language** is set to **العربية**, then
restart the game.

**The language name "العربية" in the language list is unreadable.**
That name lives in the game's own files, which no mod can change. Run the language tool and press **Fix**.

**The tutorials and the freeplay intro still show disconnected letters.**
Those texts live inside the scenario files, which no mod can reach either. The language tool patches them with the
fixed texts shipped inside this mod, after backing up the originals.

**Will a game update break the mod?**
No. The game only disables a mod when the first two version numbers change (for example 2.1 → 2.2). Steam may restore
the original tutorial files after an update or a file verification: run the tool again and press **Fix** if it appears.

**How do I switch back to English?**
In the tool, press **English**. Or in the game: **Settings → Interface → Language → English**.

**Windows warns me when I run the tool.**
The tool is not code-signed. Choose **More info → Run anyway**. Its source code is open on
[GitHub](https://github.com/F2lcon01/factorio01), and the [releases page](https://github.com/F2lcon01/factorio01/releases/latest)
lists SHA256 checksums of every file (`SHA256SUMS.txt`).

**Does it work on Linux or macOS?**
The mod does. The language tool is for Windows only; on other systems choose العربية in the game settings.

**Does it affect my save files?**
No. The mod does not change game data (checksum 0), and the tool never touches save files.

**"Couldn't get Steam auth ticket" appears in the mod list.**
It does not come from this mod. Close Steam completely and open it again.

**Where do I report a mistake in the translation?**
Open an issue on [GitHub](https://github.com/F2lcon01/factorio01/issues) with the English text and the Arabic you
expected, or use the **Discussion** tab here.
