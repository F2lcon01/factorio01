"""Machine translation for strings this project has no Arabic for (used by tools.modpack). Provider-neutral:
whatever API key the user gives. The key reaches this process only through FA_TRANSLATE_KEY (set by
tools/translate_mods.ps1); it is never written by Python. The provider is detected from the key (prefix, then a
probe of that one provider's model list), or chosen with FA_TRANSLATE_PROVIDER / FA_TRANSLATE_BASE_URL /
FA_TRANSLATE_MODEL; a key whose format names no provider is never tried on several services. A model that is
overloaded, out of quota or withdrawn hands over to the next preferred one (cfg['fallbacks']). Three request shapes:
  openai     POST {base}/chat/completions: OpenAI, Gemini, OpenRouter, Groq, DeepSeek, Mistral, xAI, Together,
             Hugging Face, Cerebras, Fireworks, NVIDIA, and local servers (Ollama, LM Studio: free, no key)
  anthropic  POST {base}/messages
  deepl      POST {base}/translate (rich-text tokens protected as XML tags)
Standard library only.  python -E -m tools.translator probe   → prints the detected provider and model"""
import json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request
from tools.lint import TOKEN_RE

_POOL = threading.Lock()   # cfg's model pool is shared by the parallel batches of one run

PROVIDERS = {  # name: (kind, base_url, model preference: first regex that matches an available model wins)
    'anthropic': ('anthropic', 'https://api.anthropic.com/v1',
                  [r'^claude-sonnet-5-5$', r'^claude-sonnet', r'^claude-opus', r'^claude-haiku']),
    'openai': ('openai', 'https://api.openai.com/v1',
               [r'^gpt-5(\.\d+)?-mini$', r'^gpt-5(\.\d+)?$', r'^gpt-4\.1-mini$', r'^gpt-4o-mini$', r'^gpt-4o$']),
    'gemini': ('openai', 'https://generativelanguage.googleapis.com/v1beta/openai',   # lite: busy-hour fallback
               [r'gemini-[\d.]+-flash$', r'gemini-[\d.]+-flash-lite$', r'gemini-flash-lite-latest$', r'gemini-[\d.]+-pro$',
                r'gemini']),
    'openrouter': ('openai', 'https://openrouter.ai/api/v1',
                   [r'^anthropic/claude-sonnet', r'^openai/gpt-5(\.\d+)?-mini$', r'^google/gemini-[\d.]+-flash$']),
    'openrouter-free': ('openai', 'https://openrouter.ai/api/v1',   # zero-priced models only (FREE_ONLY): no cost
                        [r'^google/gemma.*:free$', r'nemotron.*ultra.*:free$', r'^openrouter/free$']),
    'groq': ('openai', 'https://api.groq.com/openai/v1', [r'gpt-oss-120b', r'llama-3\.3-70b', r'llama']),
    'xai': ('openai', 'https://api.x.ai/v1', [r'^grok-\d+(\.\d+)?-mini', r'^grok-\d', r'^grok']),
    'deepseek': ('openai', 'https://api.deepseek.com/v1', [r'^deepseek-chat$', r'deepseek']),
    'mistral': ('openai', 'https://api.mistral.ai/v1', [r'^mistral-large-latest$', r'^mistral-medium', r'mistral']),
    'together': ('openai', 'https://api.together.xyz/v1', [r'Llama-3\.3-70B', r'Qwen.*Instruct']),
    'huggingface': ('openai', 'https://router.huggingface.co/v1', [r'Qwen.*Instruct', r'Llama-3\.3-70B', r'Instruct']),
    'cerebras': ('openai', 'https://api.cerebras.ai/v1', [r'gpt-oss-120b', r'llama-3\.3-70b', r'qwen', r'llama']),
    'fireworks': ('openai', 'https://api.fireworks.ai/inference/v1', [r'gpt-oss-120b', r'llama-v3p3-70b', r'qwen']),
    'nvidia': ('openai', 'https://integrate.api.nvidia.com/v1', [r'llama-3\.3-70b', r'qwen', r'instruct']),
    'deepl-free': ('deepl', 'https://api-free.deepl.com/v2', []),
    'deepl': ('deepl', 'https://api.deepl.com/v2', []),
}
# A key goes to one provider only: the one its format names, or the one the user picks. Keys that do not say whose
# they are are not tried on several services in turn (each would see it; one even echoes its last characters).
FREE_ONLY = {'openrouter-free'}
PREFIXES = [('sk-ant-', 'anthropic'), ('sk-or-', 'openrouter-free'),   # free unless the user picks paid OpenRouter
            ('AIza', 'gemini'), ('AQ.', 'gemini'),                                                      # AQ.: newer
            ('gsk_', 'groq'), ('xai-', 'xai'),                                               # Google AI Studio keys
            ('hf_', 'huggingface'), ('csk-', 'cerebras'), ('fw_', 'fireworks'), ('nvapi-', 'nvidia'),
            ('tgp_', 'together'), ('sk-', 'openai')]   # 'sk-' is also DeepSeek, Moonshot, DashScope...: OpenAI first
UNKNOWN_FORMAT = 'UNKNOWN_FORMAT'
NOT_CHAT = re.compile(r'embed|tts|whisper|dall-e|image|audio|realtime|transcribe|moderation|search|vision|guard|'
                      r'rerank|computer-use|-live|safety|lyria', re.I)
HTTP_TIMEOUT = 120
SYSTEM = """You translate the user interface of the video game Factorio (and its mods) from English into Modern Standard Arabic.
Input: a JSON object {"strings": {"<id>": "<English>"}}. Output: only a JSON object {"t": {"<id>": "<Arabic>"}} with every id.
When the input also has "source_language" (for example pt-BR), the strings are in that language: translate from it.
Rules:
- Natural, concise game-UI Arabic. Keep the meaning; do not add or drop information.
- Copy every placeholder and tag exactly as written, the same number of times: __1__, __2__, __ENTITY__iron-plate__,
  __CONTROL__build__, [item=iron-plate], [color=red]...[/color], [font=default-bold]...[/font], and the two characters \\n.
- __plural_for_parameter__1__{...}__ blocks: keep the block and its conditions; translate only the text after each '='.
- Western digits 0-9 only. No diacritics (harakat). No bidi control characters.
- Names of mods, brands and abbreviations (like P.U.M.P.) stay in Latin letters.
- Use the glossary terms when they occur."""


class TranslatorError(Exception):
    def __init__(self, message, status=None, busy=False):
        super().__init__(message)
        self.status = status   # the HTTP status, when the provider answered
        self.busy = busy       # overloaded, rate-limited or no reply in time: another model may answer


def _transient(status):
    return status in (408, 409, 429) or status >= 500


def _provider_message(raw):
    """The provider's own message, not its whole JSON (Google wraps it in a list)."""
    try:
        j = json.loads(raw)
    except ValueError:
        j = raw
    if isinstance(j, list) and j:
        j = j[0]
    err = j.get('error', j) if isinstance(j, dict) else j
    msg = err.get('message', raw) if isinstance(err, dict) else err
    return ' '.join(str(msg).split())[:160]


def _request(url, *, headers, body=None, method=None, form=False, patient=True):
    """patient=False (another model is waiting): two tries, and a timeout ends them at once."""
    tries = 4 if patient else 2
    data = None
    if body is not None:
        data = (urllib.parse.urlencode(body, doseq=True) if form else json.dumps(body, ensure_ascii=False)).encode()
        headers = {**headers, 'Content-Type': 'application/x-www-form-urlencoded' if form else 'application/json'}
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ('POST' if data else 'GET'))
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            msg = _provider_message(e.read().decode('utf-8', 'replace'))
            if not _transient(e.code):
                raise TranslatorError(f'HTTP {e.code}: {msg}', e.code) from None
            last = TranslatorError(f'HTTP {e.code} (tried {tries} times): {msg}', e.code, busy=True)   # the real reason
        except urllib.error.URLError as e:
            slow = isinstance(e.reason, TimeoutError)
            last = TranslatorError(f'timeout: no reply in {HTTP_TIMEOUT}s' if slow else f'network: {e.reason}', busy=slow)
        except TimeoutError:   # a read timeout: urllib does not wrap it in URLError
            last = TranslatorError(f'timeout: no reply in {HTTP_TIMEOUT}s', busy=True)
            if not patient:
                break
        except ConnectionError as e:   # dropped mid-reply
            last = TranslatorError(f'network: {e}')
        if attempt < tries - 1:
            time.sleep(min(2 ** attempt * 2, 30))   # transient: back off and retry
    raise last


def _auth(kind, key):
    if kind == 'anthropic':
        return {'x-api-key': key, 'anthropic-version': '2023-06-01'}
    if kind == 'deepl':
        return {'Authorization': f'DeepL-Auth-Key {key}'}
    return {'Authorization': f'Bearer {key}'}


def _is_free(item):
    """OpenRouter lists a price per token for each model: '0' for prompt and completion means no cost."""
    try:
        p = item.get('pricing') or {}
        return float(p['prompt']) == 0 and float(p['completion']) == 0
    except (KeyError, TypeError, ValueError):
        return False


def list_models(kind, base, key, free_only=False):
    if kind == 'deepl':
        _request(f'{base}/usage', headers=_auth(kind, key))   # validates the key
        return []
    data = _request(f'{base}/models', headers=_auth(kind, key))
    items = [m for m in (data.get('data', data.get('models', [])) if isinstance(data, dict) else data)
             if isinstance(m, dict) and (_is_free(m) or not free_only)]
    return [(m.get('id') or m.get('name') or '').removeprefix('models/') for m in items]


def _natural(model_id):   # 'gemini-3.10-flash' after 'gemini-3.9-flash'
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', model_id)]


def pick_models(models, prefs, n=4):
    """Chat models by preference: the newest-looking id of each preference tier first, then the rest of each tier.
    The first is used; the others stand in when it is overloaded, out of quota or withdrawn."""
    chat = [m for m in models if m and not NOT_CHAT.search(m)]
    tiers = [sorted((m for m in chat if re.search(p, m)), key=_natural, reverse=True) for p in prefs]
    out = []
    for m in [t[0] for t in tiers if t] + [m for t in tiers for m in t[1:]]:
        if m not in out:
            out.append(m)
    return (out or chat)[:n]


def pick_model(models, prefs):
    best = pick_models(models, prefs, 1)
    return best[0] if best else None


def candidates(key):
    """The provider the key's format names, or [] when it does not say (the user then picks one)."""
    if key.endswith(':fx'):
        return ['deepl-free']
    for prefix, name in PREFIXES:
        if key.startswith(prefix):
            return [name]
    if re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', key):
        return ['deepl']
    return []


def detect(key, env=os.environ):
    """→ {'provider', 'kind', 'base', 'model', 'fallbacks'}; one probe (the model list) of one provider."""
    forced, base, model = env.get('FA_TRANSLATE_PROVIDER', ''), env.get('FA_TRANSLATE_BASE_URL', ''), \
        env.get('FA_TRANSLATE_MODEL', '')
    if forced == 'deepl' and key.endswith(':fx'):
        forced = 'deepl-free'   # a free DeepL key only works on the free endpoint
    if base:   # any OpenAI-compatible server (local or hosted), unless a kind is forced
        kind = PROVIDERS[forced][0] if forced in PROVIDERS else 'openai'
        names = [(forced or 'custom', kind, base.rstrip('/'), PROVIDERS.get(forced, ('', '', []))[2])]
    elif forced:
        if forced not in PROVIDERS:
            raise TranslatorError(f'unknown provider: {forced}')
        names = [(forced, *PROVIDERS[forced])]
    else:
        names = [(n, *PROVIDERS[n]) for n in candidates(key)]
        if not names:
            raise TranslatorError(f'{UNKNOWN_FORMAT}: the key does not say which provider it is for; choose it')
    errors = []
    for name, kind, b, prefs in names:
        try:
            models = list_models(kind, b, key, free_only=name in FREE_ONLY)
        except TranslatorError as e:
            errors.append(f'{name}: {e}')
            continue
        ranked = ['deepl'] if kind == 'deepl' else [model] if model else pick_models(models, prefs)
        if not ranked:
            errors.append(f'{name}: no {"free " if name in FREE_ONLY else ""}chat model available')
            continue
        return {'provider': name, 'kind': kind, 'base': b, 'model': ranked[0], 'fallbacks': ranked[1:]}
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


def _llm_user(strings, glossary, source_lang='en'):
    msg = {'strings': strings}
    if source_lang != 'en':
        msg['source_language'] = source_lang   # a mod that ships no English for these keys
    if glossary:
        msg['glossary'] = glossary
    return json.dumps(msg, ensure_ascii=False)


def new_usage():
    """Counted for every call: what the provider reports, so savings are measured, not guessed."""
    return {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'cached_input_tokens': 0, 'chars_in': 0,
            'glossary_chars': 0}


def add_usage(total, part):
    for k, v in part.items():
        total[k] = total.get(k, 0) + v
    return total


def _chat_openai(cfg, key, user, usage, patient=True, model=None):
    body = {'model': model or cfg['model'], 'messages': [{'role': 'system', 'content': SYSTEM},
                                                          {'role': 'user', 'content': user}],
            'response_format': {'type': 'json_object'}}
    usage['requests'] += 1
    try:
        data = _request(f"{cfg['base']}/chat/completions", headers=_auth('openai', key), body=body, patient=patient)
    except TranslatorError as e:
        if e.status != 400:
            raise
        body.pop('response_format')   # some servers do not support JSON mode: the prompt asks for JSON anyway
        usage['requests'] += 1
        data = _request(f"{cfg['base']}/chat/completions", headers=_auth('openai', key), body=body, patient=patient)
    u = data.get('usage') or {}
    usage['input_tokens'] += u.get('prompt_tokens', 0)
    usage['output_tokens'] += u.get('completion_tokens', 0)
    usage['cached_input_tokens'] += (u.get('prompt_tokens_details') or {}).get('cached_tokens', 0)   # billed lower
    return data['choices'][0]['message']['content'] or ''


def _chat_anthropic(cfg, key, user, usage, patient=True, model=None):
    body = {'model': model or cfg['model'], 'max_tokens': 16000, 'system': SYSTEM,
            'messages': [{'role': 'user', 'content': user}]}
    usage['requests'] += 1
    data = _request(f"{cfg['base']}/messages", headers=_auth('anthropic', key), body=body, patient=patient)
    u = data.get('usage') or {}
    usage['input_tokens'] += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + \
        u.get('cache_creation_input_tokens', 0)
    usage['cached_input_tokens'] += u.get('cache_read_input_tokens', 0)   # billed lower
    usage['output_tokens'] += u.get('output_tokens', 0)
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


def _deepl(cfg, key, strings, usage, source_lang='en'):
    ids = [i for i, e in strings.items() if '__plural_for_parameter__' not in e]   # plural blocks: needs an LLM
    if not ids:
        return {}
    prot = [protect(strings[i]) for i in ids]
    body = {'text': [p for p, _ in prot], 'source_lang': source_lang.split('-')[0].upper(),   # pt-BR -> PT
            'target_lang': 'AR', 'tag_handling': 'xml',
            'ignore_tags': ['x'], 'show_billed_characters': True}
    usage['requests'] += 1
    usage['chars_in'] += sum(len(p) for p, _ in prot)
    data = _request(f"{cfg['base']}/translate", headers=_auth('deepl', key), body=body)
    usage['input_tokens'] += sum(t.get('billed_characters', 0) for t in data['translations'])   # DeepL bills characters
    return {i: unprotect(t['text'], toks) for i, (_, toks), t in zip(ids, prot, data['translations'])}


def _chat(cfg, key, user, usage):
    """One reply from the run's model pool, cfg['model'] then cfg['fallbacks'] (shared by the run's batches):
    - busy (429, 5xx, timeout): the next live model answers this batch, and the busy one goes to the back of the pool,
      still in it: being busy passes. Dropping each busy model for good used to walk the run off a cliff onto a model
      that no longer exists (measured: two 503s per model, then gemini-2.5-pro answered 404 and 78 strings stayed
      English).
    - 404 (withdrawn): that model leaves the pool for good.
    - anything else (401/403 refused key, 400): raised at once.
    A batch tries each live model once; then its last busy error is raised (the caller may stop the run)."""
    chat = _chat_anthropic if cfg['kind'] == 'anthropic' else _chat_openai
    tried, busy = set(), None
    while True:
        with _POOL:
            pool = [cfg['model']] + list(cfg.get('fallbacks') or [])
        live = [m for m in pool if m not in tried]
        if not live:
            raise busy
        model = live[0]
        try:
            return chat(cfg, key, user, usage, patient=len(pool) == 1, model=model)
        except TranslatorError as e:
            if not (e.busy or e.status == 404):
                raise
            tried.add(model)
            busy = e if e.busy else busy or e
            with _POOL:
                pool = [cfg['model']] + list(cfg.get('fallbacks') or [])
                if e.status == 404:
                    pool = [m for m in pool if m != model]
                elif pool[0] == model and len(pool) > 1:
                    pool = pool[1:] + [model]
                if not pool:
                    raise
                cfg['model'], cfg['fallbacks'] = pool[0], pool[1:]


def translate(cfg, key, strings, glossary=None, source_lang='en'):
    """strings {id: source text} → ({id: Arabic (logical order)}, usage); ids the reply lacks are simply absent.
    source_lang: the language of every string in this batch (English unless the mod ships none for them)."""
    usage = new_usage()
    if not strings:
        return {}, usage
    if cfg['kind'] == 'deepl':
        return _deepl(cfg, key, strings, usage, source_lang), usage
    user = _llm_user(strings, glossary, source_lang)
    usage['chars_in'] += len(SYSTEM) + len(user)
    usage['glossary_chars'] += len(json.dumps(glossary, ensure_ascii=False)) if glossary else 0
    reply = _chat(cfg, key, user, usage)
    out = parse_json_object(reply)
    out = out.get('t', out) if isinstance(out, dict) else {}
    return {i: v for i, v in out.items() if i in strings and isinstance(v, str)}, usage


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
