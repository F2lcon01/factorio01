"""Logical Arabic -> Factorio visual text (presentation forms, reversed per line)."""
import re
import arabic_reshaper

NL = '\\n'  # literal backslash-n as stored in .cfg files
HARAKAT_RE = re.compile(r'[\u064B-\u065F\u0670]')
FORMAT_RE = re.compile(r'\[/?(?:font|color)(?:=[^\]]*)?\]|__(?:CONTROL_STYLE|REMARK_COLOR)_(?:BEGIN|END)__')
FORMAT_SPLIT = re.compile(f'({FORMAT_RE.pattern})')
PLURAL_RE = re.compile(r'(__plural_for_parameter__\d+__\{)([^}]*)(\}__)')
INLINE = (r'__plural_for_parameter__\d+__\{[^}]*\}__'
          r'|__[A-Z][A-Z_]*__(?:\d+__)?(?:[a-z0-9][a-z0-9\-]*__)?'
          r'|__\d+__'
          r'|\[[a-z\-]+=[^\]]*\]')
INLINE_RE = re.compile(INLINE)
LTR = r"[A-Za-z0-9](?:[A-Za-z0-9 .,:/%+\-_'×]*[A-Za-z0-9%])?"
UNIT_RE = re.compile(f'{INLINE}|{LTR}|.', re.S)
MIRROR = dict(zip('()[]{}<>«»', ')(][}{><»«'))
_RESHAPER = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True})


def _unit(u):
    m = PLURAL_RE.fullmatch(u)
    if m:
        forms = [f.partition('=') for f in m.group(2).split('|')]
        return m.group(1) + '|'.join(f'{c}={_reverse_run(t)}' if eq else _reverse_run(c)
                                     for c, eq, t in forms) + m.group(3)
    return MIRROR.get(u, u)


def _reverse_run(text):
    return ''.join(_unit(u) for u in reversed(UNIT_RE.findall(text)))


def _visible_len(text):
    return len(INLINE_RE.sub('xx', FORMAT_RE.sub('', text)))


def wrap_logical(text, width, measure=_visible_len):
    """Hard-wrap logical text at word boundaries; tokens never split.
    `measure` maps a logical line to its width (chars by default, pixels via tools.metrics.line_px)."""
    out = []
    for para in text.split(NL):
        words, line = re.findall(f'(?:{INLINE}|\\S)+', para), ''
        for w in words:
            cand = f'{line} {w}' if line else w
            if line and measure(cand) > width:
                out.append(line)
                line = w
            else:
                line = cand
        out.append(line)
    return NL.join(out)


def to_visual(logical, *, shape=True, wrap=None, measure=_visible_len):
    text = wrap_logical(logical, wrap, measure) if wrap and measure(logical) > wrap else logical
    lines = []
    for line in text.split(NL):
        if shape:
            line = _RESHAPER.reshape(HARAKAT_RE.sub('', line))
        parts = FORMAT_SPLIT.split(line)
        lines.append(''.join(p if FORMAT_RE.fullmatch(p) else _reverse_run(p) for p in parts))
    return NL.join(lines)


def from_visual(visual):
    """Inverse of to_visual(shape=False): reversal is an involution."""
    return to_visual(visual, shape=False)
