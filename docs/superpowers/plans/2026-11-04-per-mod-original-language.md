# Per-mod "keep original language" — Implementation Plan

> Executed inline (executing-plans). Builds on `docs/superpowers/plans/2026-11-04-mods-translator-gui.md`.

**Goal:** let the player keep any one mod (or any one string) in the language the mod ships, without losing the
Arabic of the other mods and without losing that mod's stored translations.

**Architecture:** a list of excluded mods in the state folder (`STATE/excluded.json`); `resolve` marks their keys
`original` (nothing sent, nothing written); the pack and its dependencies only cover the other mods; the window shows a
checkbox per mod; an override value of `null` keeps one string original. The shared memory is untouched, so switching a
mod back to Arabic costs no request.

## Global constraints

Same as the translator plan: no deletion without permission, rollback for every change, `Parser::ParseFile` +
`ConvertFrom-Json` + `python -E -m pytest` after edits, no AI in commits, engine check (Arabic + checksum 0) before
publishing. The user asked for push, GitHub release and portal update in this request.

## Tasks

1. **Engine (`tools/modpack.py`, `tests/test_modpack.py`)**
   - `excluded() -> set[str]`, `set_excluded(name, keep_original: bool) -> list[str]` (atomic JSON in STATE).
   - `resolve(..., excluded=set())`: keys owned by an excluded mod → source `original`, no API, no Arabic;
     `overrides[key] is None` → source `original` for that key.
   - `mod_states`: state `original` («بلغته الأصلية») for excluded mods, plus `excluded: true`.
   - `fingerprint` includes the excluded list (auto-update rebuilds when it changes).
   - Report column «أصلي». CLI: `original <mod>` / `arabic <mod>`.
   - Tests: excluded mod sends nothing and is absent from the pack; switching back uses the memory (0 requests);
     `null` override; fingerprint changes; state `original`.
2. **Window (`Translate-Mods.ps1`)**: ListView checkboxes (checked = Arabic), a «اللغة» column, toggling calls the CLI and
   asks to press «ترجمة وتثبيت» to apply; guard against events while the list is filled. **CLI**
   (`tools/translate_mods.ps1`): `-KeepOriginal <mod>` / `-TranslateMod <mod>`.
3. **Checks:** unit tests; engine dump with pump kept original (English, checksum 0) and translated again (Arabic,
   0 requests); bundle rebuilt and run from the extracted zip; snapshots.
4. **Docs:** README, LANGUAGE.md, DEVLOG, README-AR.txt, portal description + FAQ, gallery image 6 refreshed.
5. **Publish:** push, release `translator-1.1.0` (new zip + arabic-tools.zip + SHA256SUMS), portal page update.

**Rollback:** tick the mod again (or delete `excluded.json` by hand); «إلغاء التثبيت (تراجع)» parks the pack;
`git revert` of the commits.
