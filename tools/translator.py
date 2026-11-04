"""Machine translation for strings this project has no Arabic for (used by tools.modpack). Provider-neutral:
whatever API key the user gives. The key reaches this process only through FA_TRANSLATE_KEY (set by
tools/translate_mods.ps1); it is never written by Python. The provider is detected from the key (prefix, then a
probe of each candidate's model list), or forced with FA_TRANSLATE_PROVIDER / FA_TRANSLATE_BASE_URL /
FA_TRANSLATE_MODEL. Three request shapes cover the providers:
  openai     POST {base}/chat/completions: OpenAI, Gemini, OpenRouter, Groq, DeepSeek, Mistral, xAI, Together,
             and local servers (Ollama, LM Studio) through FA_TRANSLATE_BASE_URL
  anthropic  POST {base}/messages
  deepl      POST {base}/translate (rich-text tokens protected as XML tags)
Standard library only.  python -E -m tools.translator probe   → prints the detected provider and model"""
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from tools.lint import TOKEN_RE

PROVIDERS = {  # name: (kind, base_url, model preference: first regex that matches an available model wins)
    'anthropic': ('anthropic', 'https://api.anthropic.com/v1',
                  [r'^claude-sonnet-5-5$', r'^claude-sonnet', r'^claude-opus', r'^claude-haiku']),
    'openai': ('openai', 'https://api.openai.com/v1',
               [r'^gpt-5(\.\d+)?-mini$', r'^gpt-5(\.\d+)?$', r'^gpt-4\.1-mini$', r'^gpt-4o-mini$', r'^gpt-4o$']),
    'gemini': ('openai', 'https://generativelanguage.googleapis.com/v1beta/openai',
               [r'gemini-[\d.]+-flash$', r'gemini-[\d.]+-flash', r'gemini-[\d.]+-pro', r'gemini']),
    'openrouter': ('openai', 'https://openrouter.ai/api/v1',
                   [r'^anthropic/claude-sonnet', r'^openai/gpt-5(\.\d+)?-mini$', r'^google/gemini-[\d.]+-flash$']),
    'groq': ('openai', 'https://api.groq.com/openai/v1', [r'gpt-oss-120b', r'llama-3\.3-70b', r'llama']),
    'xai': ('openai', 'https://api.x.ai/v1', [r'^grok-\d+(\.\d+)?-mini', r'^grok-\d', r'^grok']),
    'deepseek': ('openai', 'https://api.deepseek.com/v1', [r'^deepseek-chat$', r'deepseek']),
    'mistral': ('openai', 'https://api.mistral.ai/v1', [r'^mistral-large-latest$', r'^mistral-medium', r'mistral']),
    'together': ('openai', 'https://api.together.xyz/v1', [r'Llama-3\.3-70B', r'Qwen.*Instruct']),
    'deepl-free': ('deepl', 'https://api-free.deepl.com/v2', []),
    'deepl': ('deepl', 'https://api.deepl.com/v2', []),
}
PREFIXES = [('sk-ant-', ['anthropic']), ('sk-or-', ['openrouter']), ('AIza', ['gemini']), ('gsk_', ['groq']),
            ('xai-', ['xai']), ('sk-', ['openai', 'deepseek', 'together'])]
NOT_CHAT = re.compile(r'embed|tts|whisper|dall-e|image|audio|realtime|transcribe|moderation|search|vision|guard|'
                      r'rerank|computer-use|-live', re.I)
HTTP_TIMEOUT = 120
SYSTEM = """You translate the user interface of the video game Factorio (and its mods) from English into Modern Standard Arabic.
Input: a JSON object {"strings": {"<id>": "<English>"}}. Output: only a JSON object {"t": {"<id>": "<Arabic>"}} with every id.
Rules:
- Natural, concise game-UI Arabic. Keep the meaning; do not add or drop information.
- Copy every placeholder and tag exactly as written, the same number of times: __1__, __2__, __ENTITY__iron-plate__,
  __CONTROL__build__, [item=iron-plate], [color=red]...[/color], [font=default-bold]...[/font], and the two characters \\n.
- __plural_for_parameter__1__{...}__ blocks: keep the block and its conditions; translate only the text after each '='.
- Western digits 0-9 only. No diacritics (harakat). No bidi control characters.
- Names of mods, brands and abbreviations (like P.U.M.P.) stay in Latin letters.
- Use the glossary terms when they occur."""


class TranslatorError(Exception):
    pass


def _request(url, *, headers, body=None, method=None, form=False):
    data = None
    if body is not None:
        data = (urllib.parse.urlencode(body, doseq=True) if form else json.dumps(body, ensure_ascii=False)).encode()
        headers = {**headers, 'Content-Type': 'application/x-www-form-urlencoded' if form else 'application/json'}
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ('POST' if data else 'GET'))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (408, 409, 429) or e.code >= 500:   # transient: back off and retry
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            detail = e.read().decode('utf-8', 'replace')[:300]
            raise TranslatorError(f'HTTP {e.code}: {detail}') from None
        except urllib.error.URLError as e:
            if attempt == 3:
                raise TranslatorError(f'network: {e.reason}') from None
            time.sleep(2 ** attempt * 2)
    raise TranslatorError('gave up after retries')


def _auth(kind, key):
    if kind == 'anthropic':
        return {'x-api-key': key, 'anthropic-version': '2023-06-01'}
    if kind == 'deepl':
        return {'Authorization': f'DeepL-Auth-Key {key}'}
    return {'Authorization': f'Bearer {key}'}


def list_models(kind, base, key):
    if kind == 'deepl':
        _request(f'{base}/usage', headers=_auth(kind, key))   # validates the key
        return []
    data = _request(f'{base}/models', headers=_auth(kind, key))
    items = data.get('data', data.get('models', [])) if isinstance(data, dict) else data
    return [(m.get('id') or m.get('name') or '').removeprefix('models/') for m in items if isinstance(m, dict)]


def pick_model(models, prefs):
    chat = [m for m in models if m and not NOT_CHAT.search(m)]
    for p in prefs:
        hits = sorted((m for m in chat if re.search(p, m)), reverse=True)   # newest-looking id first
        if hits:
            return hits[0]
    return chat[0] if chat else None


def candidates(key):
    if key.endswith(':fx'):
        return ['deepl-free']
    for prefix, names in PREFIXES:
        if key.startswith(prefix):
            return names
    if re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', key):
        return ['deepl']
    return ['openai', 'mistral', 'deepseek', 'together', 'deepl']


def detect(key, env=os.environ):
    """→ {'provider', 'kind', 'base', 'model'}; probes the network unless everything is given."""
    forced, base, model = env.get('FA_TRANSLATE_PROVIDER', ''), env.get('FA_TRANSLATE_BASE_URL', ''), \
        env.get('FA_TRANSLATE_MODEL', '')
    if base:   # any OpenAI-compatible server (local or hosted), unless a kind is forced
        kind = PROVIDERS[forced][0] if forced in PROVIDERS else 'openai'
        names = [(forced or 'custom', kind, base.rstrip('/'), PROVIDERS.get(forced, ('', '', []))[2])]
    else:
        names = [(n, *PROVIDERS[n]) for n in ([forced] if forced else candidates(key))]
    errors = []
    for name, kind, b, prefs in names:
        try:
            models = list_models(kind, b, key)
        except TranslatorError as e:
            errors.append(f'{name}: {e}')
            continue
        chosen = model or pick_model(models, prefs) if kind != 'deepl' else 'deepl'
        if not chosen:
            errors.append(f'{name}: no chat model available')
            continue
        return {'provider': name, 'kind': kind, 'base': b, 'model': chosen}
    raise TranslatorError('key not accepted by: ' + '; '.join(errors))


def parse_json_object(text):
    """The first complete {...} in a reply (models sometimes wrap JSON in prose or ``` fences)."""
    start = text.find('{')
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                esc = (c == '\\' and not esc)
                if c == '"' and not esc:
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find('{', start + 1)
    raise TranslatorError('reply has no JSON object')


def _llm_user(strings, glossary):
    msg = {'strings': strings}
    if glossary:
        msg['glossary'] = glossary
    return json.dumps(msg, ensure_ascii=False)


def _chat_openai(cfg, key, user):
    body = {'model': cfg['model'], 'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}],
            'response_format': {'type': 'json_object'}}
    try:
        data = _request(f"{cfg['base']}/chat/completions", headers=_auth('openai', key), body=body)
    except TranslatorError as e:
        if not str(e).startswith('HTTP 400'):
            raise
        body.pop('response_format')   # some servers do not support JSON mode: the prompt asks for JSON anyway
        data = _request(f"{cfg['base']}/chat/completions", headers=_auth('openai', key), body=body)
    return data['choices'][0]['message']['content'] or ''


def _chat_anthropic(cfg, key, user):
    body = {'model': cfg['model'], 'max_tokens': 16000, 'system': SYSTEM, 'messages': [{'role': 'user', 'content': user}]}
    data = _request(f"{cfg['base']}/messages", headers=_auth('anthropic', key), body=body)
    if data.get('stop_reason') == 'refusal':
        raise TranslatorError('the model declined the request')
    return ''.join(b.get('text', '') for b in data.get('content', []) if b.get('type') == 'text')


def protect(text):
    """Rich-text tokens → <x i="n"/> for DeepL; returns (protected text, tokens)."""
    tokens = []

    def sub(m):
        tokens.append(m.group(0))
        return f'<x i="{len(tokens) - 1}"/>'
    return TOKEN_RE.sub(sub, text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')), tokens


def unprotect(text, tokens):
    text = re.sub(r'<x i="(\d+)"\s*/>', lambda m: tokens[int(m.group(1))], text)
    return text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def _deepl(cfg, key, strings):
    ids = [i for i, e in strings.items() if '__plural_for_parameter__' not in e]   # plural blocks: needs an LLM
    if not ids:
        return {}
    prot = [protect(strings[i]) for i in ids]
    body = {'text': [p for p, _ in prot], 'source_lang': 'EN', 'target_lang': 'AR', 'tag_handling': 'xml',
            'ignore_tags': ['x']}
    data = _request(f"{cfg['base']}/translate", headers=_auth('deepl', key), body=body)
    return {i: unprotect(t['text'], toks) for i, (_, toks), t in zip(ids, prot, data['translations'])}


def translate(cfg, key, strings, glossary=None):
    """strings {id: English} → {id: Arabic (logical order)}; ids the reply lacks are simply absent."""
    if not strings:
        return {}
    if cfg['kind'] == 'deepl':
        return _deepl(cfg, key, strings)
    user = _llm_user(strings, glossary)
    reply = _chat_anthropic(cfg, key, user) if cfg['kind'] == 'anthropic' else _chat_openai(cfg, key, user)
    out = parse_json_object(reply)
    out = out.get('t', out) if isinstance(out, dict) else {}
    return {i: v for i, v in out.items() if i in strings and isinstance(v, str)}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    key = os.environ.get('FA_TRANSLATE_KEY', '')
    if not key:
        sys.exit('FA_TRANSLATE_KEY is not set')
    try:
        print(json.dumps(detect(key)))
    except TranslatorError as e:
        sys.exit(f'translator: {e}')


if __name__ == '__main__':
    if sys.argv[1:] == ['probe']:
        main()
    else:
        sys.exit('usage: python -E -m tools.translator probe')
