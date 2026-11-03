# تغيير لغة Factorio: العربية ↔ الإنجليزية

> **قبل أي تغيير: أغلق اللعبة.** اللعبة تحفظ إعداداتها عند الإغلاق، فلو غيّرت اللغة وهي مفتوحة ستعيدها كما كانت.

---

## الطريقة الأسهل: نافذة تغيير اللغة

1. افتح مجلد المشروع: `C:\Users\a0551\Desktop\factorio-arabic`
2. انقر مرتين على **`Change-Language.cmd`**
3. سيطلب Windows صلاحيات المدير — اضغط **«نعم»**
4. تظهر نافذة فيها زرّان:
   - **العربية** — تحوّل اللعبة للعربية، وتتأكد تلقائياً أن مود الترجمة مثبّت ومفعّل، وأن اسم اللغة ونصوص الدروس سليمة
   - **English** — تعيد اللعبة للإنجليزية
5. تظهر رسالة «تم» ومكان النسخة الاحتياطية. افتح اللعبة.

> تُحفظ نسخة احتياطية من الإعدادات قبل كل تغيير في `backups\settings-<التاريخ>`.

---

## من داخل اللعبة

الإعدادات (Settings) ← الواجهة (Interface) ← اللغة (Language) ← اختر **العربية** أو **English**.

---

## بالأمر (بلا نافذة)

افتح PowerShell داخل مجلد المشروع ثم:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -STA -File .\Change-Language.ps1 -Language ar   # العربية
powershell -NoProfile -ExecutionPolicy Bypass -STA -File .\Change-Language.ps1 -Language en   # الإنجليزية
```

---

## التحديث التلقائي مع تحديثات اللعبة

**ماذا يفعل:** عند تسجيل الدخول لويندوز وكل 6 ساعات يفحص نسخة اللعبة:

| الحالة | ما يحدث تلقائياً |
|---|---|
| نسخة اللعبة تغيّرت (مثلاً 2.1.24 ← 2.1.25) | يعيد بناء المود **بنفس رقم نسخة اللعبة**، ويثبّته، ويفحصه داخل المحرك |
| ظهرت نصوص جديدة في اللعبة | يأخذ الترجمة الرسمية لها إن وُجدت ويصلها بحروف متصلة؛ وما لا ترجمة له يظهر بالإنجليزي ويُسجَّل في `reports\auto-update.md` |
| تحديث رئيسي (مثلاً 2.2) | يحدّث خانة التوافق في المود حتى لا تعطّله اللعبة |
| Steam أعاد ملفات اللعبة الأصلية (تحديث أو «التحقق من الملفات») | يعيد ترقيع نصوص الدروس واسم اللغة |
| لا شيء تغيّر | ينتهي خلال ثانية دون أي تعديل |
| اللعبة مفتوحة | يتخطى ويحاول في المرة القادمة |

**السجل:** `reports\auto-update.log`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\auto_update.ps1              # تشغيل الآن
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\auto_update.ps1 -Register    # تفعيل التلقائي
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\auto_update.ps1 -Unregister  # إيقاف التلقائي
```

> ملاحظة صادقة: النصوص الجديدة **غير المترجمة رسمياً** لا يمكن ترجمتها تلقائياً بلا مترجم؛ تظهر بالإنجليزي
> حتى تُترجم، وقائمتها في `reports\auto-update.md`.

---

## حل المشكلات

| المشكلة | الحل |
|---|---|
| النافذة تقول «أغلق اللعبة أولاً» | أغلق Factorio تماماً ثم أعد المحاولة |
| «Couldn't get Steam auth ticket» داخل قائمة المودات | ليست من المود؛ أغلق Steam كلياً وأعد فتحه. المود يعمل رغمها |
| اسم اللغة يظهر بحروف مقطعة في القائمة | اختر «العربية» من النافذة؛ تصلحه تلقائياً |
| بعد تحديث Steam عادت نصوص الدروس منفصلة | شغّل `tools\auto_update.ps1` أو اختر «العربية» من النافذة |
| انقر مرتين على `.ps1` فيفتح المفكرة | استخدم `Change-Language.cmd` بدلاً منه |

---

## التراجع الكامل عن كل شيء

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\auto_update.ps1 -Unregister
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\install.ps1 -Uninstall
python -E -m tools.scenarios restore
powershell -NoProfile -ExecutionPolicy Bypass -STA -File .\Change-Language.ps1 -Language en
```
