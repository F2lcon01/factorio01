# Review summary (2026-11-03)

| Source | Keys | Automated checks | Human-read sample |
|---|---|---|---|
| Prototype names (agent) | 455 | `tools.terms check` errors=0 | 30 (`tools.review terms 30`): accurate, glossary-consistent |
| Scenarios (agent) | 64 + 31 fixes | `tools.scenarios merge` rejected=0, build OK | 10 rows: accurate, glossary names unified |
| Batch 001 (agent) | 120 | `check_batch` errors=0 | 12 (`review-001.md`): accurate; old chest wording / 1-2-rest plurals only in raw output, fixed in src by `term_migrations` + `tools.plurals` |
| Batches 002–003 (agents) | 240 | `check_batch` errors=0 | 27 (`review-002.md`, `review-003.md`): accurate |
| Batches 004–018, 019 (written inline) | 1 795 | `check_batch` errors=0 each | every line written and read by the translator |

Defects found by review/scans in the **official** translation and fixed: barrel names, provider chests, cliff/«كليف»,
Eastern digits, speaker notes (→ solfège), 4 reversed lines, «فيكتوريو», stray «منصة الصواريخ.» in the freeplay intro,
double period in `multiplayer/your-version`, typo-ridden achievement `it-stinks-and-they-dont-like-it`.

Final gates: lint errors=0 (6 modules) · pytest 43 passed · engine exact=1864 ok=1570 exception=8 english=0 unshaped=0 ·
scenarios patched 23/23 · engine reads patched scenario text · GUI screenshot of the patched freeplay intro
(`reports/screens/phase4-scenario-zoom.png`, launched through Steam with the user's confirmation).
