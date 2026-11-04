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
    lines, sec = [], None
    for full in order:
        if full not in values:
            continue
        s, k = full.split('/', 1)
        if s != sec:
            if s:
                lines.append(f'[{s}]')
            sec = s
        lines.append(f'{k}={values[full]}')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')  # LF like the game's files
