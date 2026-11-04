# Mods Translator GUI — Implementation Plan

> Executed inline in the session that wrote it (executing-plans). Spec:
> `docs/superpowers/specs/2026-11-04-mods-translator-gui-design.md`.

**Goal:** a WinForms (PS 5.1, Arabic RTL) window over `tools/modpack.py` with a shared translation memory, a term
base, incremental translation and measured token use; shipped to players with an embedded Python via GitHub Releases.

**Architecture:** Python stays the engine (`modpack` + new `memory`); PowerShell owns the key (DPAPI), the window,
installation and the player launcher; the window runs Python as a child process and polls a progress file.

**Tech stack:** Python 3.13 standard library + arabic_reshaper + fontTools; Windows PowerShell 5.1 / 7, WinForms.

## Global constraints

- No deletion without the user's permission; every change has a rollback path.
- After each edit: `Parser::ParseFile` (both PowerShell versions), `ConvertFrom-Json`, `python -E -m pytest`
  (run with `-p no:cacheprovider --basetemp <scratch>`: the user's pytest temp dirs lost their permissions).
- Commits never mention AI; no `git push` and no mod-portal publish without asking.
- API keys only DPAPI-encrypted outside the project; Python receives them through the environment.
- Engine check before publishing: isolated `--dump-prototype-locale`, Arabic text and `Checksum ... : 0`.
- The mod portal rejects executables: the tool ships as a GitHub release asset.
- `FactorioArabic.psm1` and `tools/*.ps1` stay ASCII; files with Arabic UI text are UTF-8 with BOM.

---

### Task 1: translation memory and term base (`tools/memory.py`)

**Files:** create `tools/memory.py`, `tests/test_memory.py`.

**Produces:**
- `norm(en: str) -> str` (whitespace collapsed, stripped).
- `class TranslationMemory(path)`: `.get(en) -> str|None` (exact, then case-insensitive), `.put(en, ar, src, model='')`,
  `.save()`, `.import_legacy_cache(cache: dict, en_by_key: dict) -> int`, `len()`.
- `base_memory() -> dict[str, str]` (normalized lower English → logical Arabic): `src/ar` when present, else the
  installed `arabic-complete` locale (folder or zip) via NFKC + `from_visual`.
- `term_base(glossary: dict, base_pairs: dict) -> dict[str, str]` and `terms_for(texts, tb, limit=60) -> dict`.

**Tests:** exact/case-insensitive hits; save/load round trip; legacy import keeps only matching hashes; base memory
from an installed-mod fixture equals the logical text; term filter is word-bounded and longest-first.

### Task 2: usage metering in `tools/translator.py`

**Produces:** `translate(cfg, key, strings, glossary=None) -> (dict, dict)`; usage keys `requests`, `input_tokens`,
`output_tokens`, `chars_in`, `glossary_chars`. OpenAI `usage.prompt_tokens/completion_tokens`, Anthropic
`usage.input_tokens/output_tokens`, DeepL `billed_characters` (requested with `show_billed_characters`).

**Tests:** update the existing three request-shape tests to unpack `(out, usage)` and assert the numbers.

### Task 3: modpack on the memory, per-mod states, progress, savings

**Files:** modify `tools/modpack.py`, `tests/test_modpack.py`.

**Consumes:** Task 1, Task 2. **Produces:**
- `resolve(mods, *, base, memory, overrides, terms, translate, progress=None, log=print) -> (arabic, owner, rows)`;
  rows gains `usage` and `from_memory` (count of strings served by the shared memory).
- `mod_states(mods, manifest, memory, base, overrides) -> list[dict]` with `name, title, version, strings, arabic,
  pending, changed, state ∈ {translated,new,changed,pending}`.
- `STATE` from `FA_STATE_DIR` (default `work/modpack`); files `memory.json`, `manifest.json`, `usage.json`,
  `translator.json`; legacy `cache.json` imported once, never deleted.
- `FA_PROGRESS_FILE`: JSON lines `{"stage","done","total"}`.
- CLI: `build [--offline]`, `status` (adds `"mods": [...states]`), unchanged output keys kept.
- Report section «التوفير» with requests, tokens, glossary share, memory hits and estimated tokens saved.

**Tests:** second resolve over the same mods calls the translator 0 times; a changed English string alone is sent;
overrides never enter the memory; states for new/changed/pending/translated.

### Task 4: integration test with a local provider

**Files:** `tests/test_modpack_e2e.py` — an `http.server` thread speaking the OpenAI chat shape (returns Arabic that
keeps every token), counting requests; full `build()` twice on fixture mods: run 1 > 0 requests, run 2 = 0.

### Task 5: PowerShell module: key, Python, pack install

**Files:** modify `tools/FactorioArabic.psm1`, `tools/translate_mods.ps1`, `tools/install.ps1` (unchanged API).

**Produces:** `Get-FAStateDir`, `Get-FATranslatorKey`, `Save-FATranslatorKey([securestring])`,
`Remove-FATranslatorKey`, `Install-FAPack($Path)`, `Uninstall-FAPack($Name)`, `Invoke-FAPython` using
`<tools>\python\python.exe` + `<tools>\app` when present. `translate_mods.ps1` uses them (same switches).

### Task 6: the window (`Translate-Mods.ps1` + `.cmd`)

UTF-8 BOM, STA, RTL. ListView of mods and states; key box (hidden), save+check, forget; Translate button with
ProgressBar fed by the progress file (WinForms timer, child process); summary from `modpack summary`; open report;
rollback button. `-Snapshot <png>`, `-UserAppData`, `-PreviewBusy` for documentation shots. Button in
`Change-Language.ps1` opens it through `explorer.exe` (not elevated) or the releases page.

### Task 7: player bundle

**Files:** create `tools/vendor.py` (download + SHA256 pins into `work/vendor/`, gitignored); extend
`tools/bundle.py` with `translator_zip()` → `dist/arabic-mods-translator.zip`: launcher files, `app/tools/*.py`,
`app/glossary.json`, `python/` (embed zip + `python313._pth` with `..\app` and `Lib\site-packages`) and the two
wheels unpacked. Smoke test: extract to temp, run an offline build and a stub-provider build with the embedded Python.

### Task 8: game test, measurement, screenshots, docs, release prep

Engine dump with the built pack (Arabic + checksum 0); measured run 1 / run 2 with the stub provider on the real
mods folder; real window screenshots; README (readme-designer), LANGUAGE.md, DEVLOG, portal description/FAQ/image;
release notes. Commit. Then ask before push, release and portal publish.
