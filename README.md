# factorio-arabic

تعريب كامل لـ Factorio 2.1 (+ Space Age) بحروف متصلة واتجاه قراءة صحيح، كمود `arabic-complete` + رقعة نصوص السيناريوهات.

## لماذا هذا التصميم
- المحرك لا يشكّل العربية ولا يعرف اليمين لليسار → نبني النص بأشكال العرض المتصلة ونعكسه سطراً سطراً.
- اللفّ التلقائي للمحرك يقلب ترتيب الأسطر → نلفّ مسبقاً بالبكسل (`WRAP = 460`، مُعايَر داخل اللعبة).
- المود لا يتجاوز نصوص السيناريو (مُثبت) → `tools/scenarios.py` يرقّعها بنسخة احتياطية واسترجاع مطابق بايتاً بايتاً.
- الأدلة: `reports/spike.md`، `reports/verify-game.md`.

## المصدر
`src/ar/*.cfg` و`src/scenarios/**` نص عربي **منطقي عادي** (كما يُكتب). لا تحرر ملفات `dist/` أبداً.

## خط الإنتاج (بالترتيب)
```powershell
python -E -m tools.import_official          # الرسمي → منطقي + work/todo.jsonl
python -E -m tools.glossary --apply-decisions # توحيد المصطلحات (glossary_decisions.json)
python -E -m tools.terms apply              # أسماء النماذج المترجمة مرة واحدة
python -E -m tools.batches                  # تقسيم الباقي
python -E -m tools.merge NNN                # لكل دفعة مترجمة
python -E -m tools.corrections              # term_migrations + corrections.json + قاعدة الجمع + أرقام لاتينية + سولفيج
python -E -m tools.lint                     # يجب: errors=0
python -E -m pytest                         # كل الاختبارات
python -E -m tools.verify_game 1.0.0        # داخل المحرك: english=0 unshaped=0
python -E -m tools.visual_check 1.0.0       # لقطات شاشة حقيقية → reports/screens
python -E -m tools.build 1.0.0              # dist/arabic-complete_1.0.0
powershell -NoProfile -File tools\install.ps1 -Version 1.0.0   # تثبيت + تفعيل (نسخة احتياطية لـ mod-list.json)
python -E -m tools.scenarios build; python -E -m tools.scenarios apply   # رقعة السيناريوهات
python -E -m tools.scenario_check           # المحرك يقرأ نص السيناريو المرقّع (بلا نافذة وبلا Steam)
```

> التثبيت بـ PowerShell لا Python: نسخة Python من Microsoft Store تحوّل كتاباتها تحت `%APPDATA%`
> إلى نسخة خاصة لا تراها اللعبة (مُثبت). `tools/install.py` يرفض عمداً ويشير إلى `install.ps1`.

## الاسترجاع
```powershell
powershell -NoProfile -File tools\install.ps1 -Uninstall   # تعطيل + نقل المود إلى %APPDATA%\Factorio\mods-parked (لا حذف)
python -E -m tools.scenarios restore     # إعادة ملفات السيناريو الأصلية بايتاً بايتاً (مُختبر على اللعبة الحقيقية)
```

## استثناءات موثّقة (لا تُترجم بملفات اللغة)
8 أسماء مكتوبة حرفياً في كود اللعبة نفسها (`localised_name = "dummy"` في `trains.lua`/`enemies.lua`، وخطأ في
`explosions.lua:7885`) — كيانات داخلية لا تظهر للاعب. مسجلة في `tools/verify_game.py: EXCEPTIONS`.
أو من Steam: «التحقق من سلامة ملفات اللعبة» يعيد ملفات السيناريو الأصلية.

## بعد كل تحديث للعبة
```powershell
python -E -m tools.sync                     # مفاتيح جديدة/متغيرة → work/todo.jsonl
# ترجمة → merge → lint → pytest → verify_game → build <ver+1> → install
python -E -m tools.sync --refresh-snapshot
python -E -m tools.scenarios status         # إن ظهر 'other' فالتحديث استبدل الملفات: أعد build + apply
```

## حدود لا يحلّها مود
محاذاة النص لليسار · البحث بالعربي داخل اللعبة · اسم اللغة في قائمة اللغات · نص الدردشة.
