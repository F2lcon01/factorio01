# Translation brief — Factorio 2.1 (+ Space Age) → Arabic

Project root: `C:\Users\a0551\Desktop\factorio-arabic` (always use absolute paths).
You translate ONE batch `NNN` (given in your task). Touch no file except `work\out\NNN.jsonl`.
Do not run `tools.merge`, git, or the game. Other translators work on other batches at the same time.

## Input
- `work\batches\NNN.jsonl` — one JSON object per line: `module`, `key` (`section/key`), `en` (English source),
  `hint` (a previous, defective Arabic translation in normal reading order — may be empty), `reason`
  (`missing` | `tokens` | `direction` | `not-involutive` | `no-arabic` | `forbidden-char`).
- `work\batches\NNN.glossary.json` — mandatory terms for this batch (English lower-case → Arabic).
- `glossary.json` (743 terms) and the existing translations in `src\ar\*.cfg` — search them (Grep) to stay
  consistent with terms already used in the game (e.g. how "inserter", "belt", "assembling machine",
  "space platform", "quality" are translated).

## Output
`work\out\NNN.jsonl` — UTF-8 JSON Lines, **same number of lines, same order** as the input, each:
`{"module": "...", "key": "...", "ar": "..."}` (copy `module` and `key` exactly).
JSON escaping: the English text contains the two characters backslash + n (`\n`) as a line break marker; in the
input JSON it appears as `"\\n"`. Your `ar` must contain the same number of these markers, written the same way.

## Rules
1. Write normal Arabic in normal reading order, exactly as a person types it. NEVER reverse text, never use
   Arabic presentation forms (U+FB50–FDFF, U+FE70–FEFF), never add direction marks (U+200E/F, U+202A–E, U+2066–9).
   The build tool shapes and reverses automatically.
2. Copy every token byte-for-byte and keep the same count of each: `__1__`, `__2__`, `__CONTROL__name__`,
   `__ALT_CONTROL__1__name__`, `__CONTROL_MODIFIER__name__`, `__ITEM__name__`, `__ENTITY__name__`, `__TILE__name__`,
   `__FLUID__name__`, `__PLANET__name__`, `__CONTROL_STYLE_BEGIN__`/`__CONTROL_STYLE_END__`,
   `__REMARK_COLOR_BEGIN__`/`__REMARK_COLOR_END__`, rich text `[item=x]`, `[entity=x]`, `[tip=x]`, `[img=x]`,
   `[font=x]…[/font]`, `[color=x]…[/color]` (keep each pair wrapped around the matching Arabic words).
   Never translate words inside tokens.
3. Plurals: keep `__plural_for_parameter__N__{...}__`. Every form is `condition=text`; allowed conditions are numbers,
   `ends in N`, and `rest`. Give Arabic forms, e.g. `__plural_for_parameter__1__{1=عنصر واحد|2=عنصران|rest=عناصر}__`.
   The plural block counts as one token: the count of plural blocks must match the English.
4. Glossary terms are mandatory. You may adapt the definite article or grammatical case («الحزام»/«حزام»), never
   the word itself. Planet and proper names: transliterate as the glossary does (نوفيس، فولكانوس، فولغورا، غليبا، أكويلو).
5. Style: Modern Standard Arabic, short and clear game-UI wording. Imperative for actions (اضغط، ضع، اسحب، اختر).
   Arabic punctuation: «،» and «؟»; the full stop stays «.». Western digits (0-9). No harakat unless a word would be
   ambiguous without them. Keep keyboard keys and brands in Latin (Ctrl, Shift, Alt, Steam, Xbox, PlayStation, LAN).
6. `hint` non-empty → it is an earlier translation with the defect named in `reason`: reuse its correct wording,
   fix the defect (broken tokens, English left over, wrong word order caused by reversed text, etc.).
7. Every `ar` must contain Arabic letters (except pure numbers/tokens/brand names where the English has no real words).

## Validate (mandatory, repeat until `errors=0`)
```powershell
Push-Location 'C:\Users\a0551\Desktop\factorio-arabic'; python -E -m tools.check_batch NNN; Pop-Location
```
`ERROR` lines must all be fixed. `WARN` lines are glossary hints: follow them unless grammar requires an
inflected form of the same term.

## Report back (short)
The final `errors=… warnings=…` line from the checker, the number of lines written, and up to 5 strings you were
unsure about (key + your choice). Do not paste the translations.
