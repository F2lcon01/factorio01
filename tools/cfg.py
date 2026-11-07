"""Read/write Factorio .cfg locale files; keys are 'section/key' ('' section = root)."""
import re
from pathlib import Path

SECTION_RE = re.compile(r'^\[([^\]]+)\]\s*$')


def read_cfg(path) -> dict[str, str]:
    return parse_cfg(Path(path).read_text(encoding='utf-8-sig'))


def parse_cfg(text: str) -> dict[str, str]:
    """Same as read_cfg, for text already in memory (locale files inside a mod's zip)."""
    out, sec = {}, ''
    for line in text.lstrip('﻿').splitlines():
        if not line or line[0] in ';#':
            continue
        m = SECTION_RE.match(line)
        if m:
            sec = m.group(1)
        elif '=' in line:
            k, v = line.split('=', 1)
            out[f'{sec}/{k}'] = v
    return out


def write_cfg(path, values: dict[str, str], order: list[str]) -> None:
    """Each section once, in first-appearance order (root keys first, before any header). The game refuses a locale
    file whose section repeats ('Duplicate key "string-mod-setting" in property tree at ROOT' → the whole mod fails
    to load): a mod's keys come from several files (FactorySearch has [string-mod-setting] in two), so `order` can
    leave a section and come back to it."""
    sections = {}
    for full in order:
        if full in values:
            s, k = full.split('/', 1)
            sections.setdefault(s, []).append(f'{k}={values[full]}')
    lines = sections.pop('', [])
    for s, entries in sections.items():
        lines += [f'[{s}]'] + entries
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')  # LF like the game's files
