# Draft — forums.factorio.com › Translations (or a private message to the Crowdin project manager)

**Title:** Arabic: 2,410 missing strings + 392 fixes ready for import (Factorio 2.1 + Space Age)

Hello,

The official Arabic translation currently covers about 70% of Factorio 2.1 (Space Age about 15%). I have prepared a
complete set for all six modules (core, base, elevated-rails, quality, recycler, space-age):

- **2,410** strings that are missing today,
- **392** corrections to existing strings (broken parameters such as `__CONTROL__…__`, lines stored in the wrong
  direction, untranslated words, inconsistent terms),
- **4,798** strings unchanged.

The files follow the convention already used by the shipped Arabic locale (text stored in visual order, not shaped),
so they can be imported as they are. A review sheet lists every new and changed string next to the English and the
current official text:

- `arabic-crowdin_1.0.0.zip` — `locale/ar/<module>.cfg`, same keys and order as `locale/en`
- `crowdin-diff.csv` — module, key, kind (new/changed), English, official Arabic, proposed Arabic

Since uploading files is limited to project managers, could the Arabic strings be imported as suggestions (or could I
be given proofreader access to submit them)? I am happy to go through any string a proofreader flags.

Note: Arabic letters are not shaped by the engine, so even a complete Crowdin translation shows disconnected letters
in game. The mod `arabic-complete` on the mod portal ships the same text pre-shaped for players who want that today.

Thank you,
Falcon
