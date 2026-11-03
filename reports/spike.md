# Phase 0 — in-game verification (2026-11-03, Factorio 2.1.24)

Method: `tools/harness.py` launches the real game (GUI) in an isolated env (`%TEMP%\fa-harness`,
`-c` own config with `locale=ar`, own `write-data`, own `--mod-directory`, `--load-scenario base/freeplay`)
and a test mod draws labels with style `tooltip_label` (356px, `data/core/prototypes/style.lua:959-965`),
then `game.take_screenshot{show_gui=true}`. Screens: `reports/screens/phase0-*.png` (not in git; rerun
`python -E -m tools.spike` / `python -E -m tools.calibrate`).

| # | Question | Result | Evidence |
|---|---|---|---|
| 1 | Presentation forms render connected | PASS | `phase0-basics`: «لعب فردي», «صفيحة حديد», «العربية لا إله إلا الله» connected; official core text in the research hint is disconnected |
| 2 | Mod overrides `core` GUI keys (non-prototype) | PASS | `gui-menu.single-player-menu` shows our text |
| 3 | Mod overrides scenario keys (`freeplay` `msg-intro`) | **FAIL** | label `{"msg-intro"}` shows the official freeplay paragraph, not ours → **Task 12 required** |
| 4 | Engine word-wrap keeps reading order | **FAIL** | official `msg-intro` and our `engine-wrapped` paragraph show the last line on top → pre-wrap is mandatory |
| 5 | Pre-wrapped text reads top-down | PASS | `phase0-paragraph`: prewrapped block correct order |
| 6 | Tokens / brackets / numbers order | PASS | «اضغط [الزر الأيسر] لوضع [icon] على الحزام (الأحمر).», «1.5», «20٪» |
| 7 | Harakat removed, lam-alef ligature | PASS | «العربية لا إله إلا الله» |

## Wrap calibration (tooltip_label 356px)

`tools.metrics.line_px` (glyph advances at 14px from the game's fonts) over-estimates rendered Arabic width.
Single line at measured 418 and 460; wrapped at 518 (`phase0-calibrate`). Decision: **WRAP = 460** (line_px units).

## Plan deviations

- Pixel-based wrap (`wrap_logical(..., measure=line_px)`) instead of a character count: «ا» = 3.3px vs «س» = 16.9px.
- Visual checks are automated with the harness instead of manual screenshots.
- GUI launches re-enter through Steam (`steam://run/427520`, arguments preserved): the harness tracks the isolated
  write dir, kills only processes whose command line contains `fa-harness`, and aborts if isolated write-data
  is not in use (a config with duplicate keys is silently ignored by the game — guarded by `_assert_valid_ini`).
- Same `re.sub` backslash bug as the plan's Task 7 code: replacement must be a lambda.
