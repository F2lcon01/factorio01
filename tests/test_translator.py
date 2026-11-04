import io, json, urllib.error
import pytest
from tools import translator


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_urlopen(routes, seen):
    def urlopen(req, timeout=None):
        seen.append(req)
        for (method, suffix), reply in routes.items():
            if req.get_method() == method and req.full_url.endswith(suffix):
                if isinstance(reply, int):
                    raise urllib.error.HTTPError(req.full_url, reply, 'err', {}, io.BytesIO(b'{"error":"x"}'))
                return _Resp(json.dumps(reply).encode())
        raise urllib.error.HTTPError(req.full_url, 401, 'unauthorized', {}, io.BytesIO(b'{}'))
    return urlopen


@pytest.mark.parametrize('key,first', [('sk-ant-abc', 'anthropic'), ('sk-or-v1-x', 'openrouter'), ('AIzaXYZ', 'gemini'),
                                       ('gsk_1', 'groq'), ('xai-1', 'xai'), ('sk-proj-1', 'openai'), ('abc:fx', 'deepl-free'),
                                       ('12345678-1234-1234-1234-123456789abc', 'deepl'), ('hf_x', 'huggingface'),
                                       ('csk-x', 'cerebras'), ('fw_x', 'fireworks'), ('nvapi-x', 'nvidia'),
                                       ('AQ.Ab8RN6x', 'gemini')])   # the newer Google AI Studio key format
def test_provider_candidates_from_the_key(key, first):
    assert translator.candidates(key)[0] == first


def test_a_key_is_sent_to_one_provider_only(monkeypatch):
    seen = []
    monkeypatch.setattr(translator.urllib.request, 'urlopen', _fake_urlopen({}, seen))   # every provider refuses
    with pytest.raises(translator.TranslatorError, match='UNKNOWN_FORMAT'):
        translator.detect('Ab3dEf6hIj9kLm2nOp5qRs8tUv1wXyZ0', env={})                 # says nothing about its owner
    assert seen == []                                                                   # so it is sent nowhere
    with pytest.raises(translator.TranslatorError, match=r'^key not accepted by: openai: HTTP 401'):
        translator.detect('sk-something', env={})
    assert [r.full_url for r in seen] == ['https://api.openai.com/v1/models']          # one provider, one request


def test_a_chosen_provider_is_probed_and_a_chat_model_picked(monkeypatch):
    seen = []
    routes = {('GET', 'api.deepseek.com/v1/models'): {'data': [{'id': 'deepseek-embed'}, {'id': 'deepseek-chat'}]}}
    monkeypatch.setattr(translator.urllib.request, 'urlopen', _fake_urlopen(routes, seen))
    cfg = translator.detect('sk-unknown', env={'FA_TRANSLATE_PROVIDER': 'deepseek'})
    assert cfg == {'provider': 'deepseek', 'kind': 'openai', 'base': 'https://api.deepseek.com/v1', 'model': 'deepseek-chat',
                   'fallbacks': []}
    assert len(seen) == 1 and seen[0].get_header('Authorization') == 'Bearer sk-unknown'


def test_provider_error_message_is_short_and_readable(monkeypatch):
    def urlopen(req, timeout=None):
        body = b'{"error": {"message": "Incorrect API key provided: sk-abc***xyz.", "type": "invalid_request_error"}}'
        raise urllib.error.HTTPError(req.full_url, 401, 'unauthorized', {}, io.BytesIO(body))
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    with pytest.raises(translator.TranslatorError) as e:
        translator.detect('sk-abc', env={})
    assert str(e.value) == 'key not accepted by: openai: HTTP 401: Incorrect API key provided: sk-abc***xyz.'


def test_a_free_deepl_key_goes_to_the_free_endpoint_even_when_deepl_is_chosen(monkeypatch):
    seen = []
    monkeypatch.setattr(translator.urllib.request, 'urlopen',
                        _fake_urlopen({('GET', 'api-free.deepl.com/v2/usage'): {'character_count': 0}}, seen))
    assert translator.detect('k:fx', env={'FA_TRANSLATE_PROVIDER': 'deepl'})['provider'] == 'deepl-free'


def test_detect_honours_a_custom_base_url_and_model(monkeypatch):
    routes = {('GET', 'localhost:11434/v1/models'): {'data': [{'id': 'qwen'}]}}
    monkeypatch.setattr(translator.urllib.request, 'urlopen', _fake_urlopen(routes, []))
    cfg = translator.detect('x', env={'FA_TRANSLATE_BASE_URL': 'http://localhost:11434/v1/', 'FA_TRANSLATE_MODEL': 'llama'})
    assert cfg['base'] == 'http://localhost:11434/v1' and cfg['model'] == 'llama' and cfg['kind'] == 'openai'


def test_pick_model_skips_non_chat_models():
    models = ['text-embedding-3', 'gpt-4o-mini', 'gpt-5-mini', 'gpt-5.1-mini', 'tts-1']
    assert translator.pick_model(models, translator.PROVIDERS['openai'][2]) == 'gpt-5.1-mini'


def test_openai_shape_falls_back_without_json_mode(monkeypatch):
    seen, calls = [], {'n': 0}

    def urlopen(req, timeout=None):
        seen.append(json.loads(req.data))
        calls['n'] += 1
        if calls['n'] == 1:
            raise urllib.error.HTTPError(req.full_url, 400, 'bad', {}, io.BytesIO(b'response_format unsupported'))
        reply = '```json\n{"t": {"a": "تأكيد", "z": "extra"}}\n```'
        return _Resp(json.dumps({'choices': [{'message': {'content': reply}}],
                                 'usage': {'prompt_tokens': 50, 'completion_tokens': 9}}).encode())
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    cfg = {'kind': 'openai', 'base': 'https://x/v1', 'model': 'm'}
    out, usage = translator.translate(cfg, 'k', {'a': 'Confirm'})
    assert out == {'a': 'تأكيد'}                                  # ids not asked for are dropped
    assert 'response_format' in seen[0] and 'response_format' not in seen[1]
    assert usage['requests'] == 2 and usage['input_tokens'] == 50 and usage['output_tokens'] == 9


def test_anthropic_shape(monkeypatch):
    seen = []
    reply = {'content': [{'type': 'thinking', 'thinking': ''}, {'type': 'text', 'text': '{"t": {"a": "إلغاء"}}'}],
             'stop_reason': 'end_turn', 'usage': {'input_tokens': 100, 'output_tokens': 15, 'cache_read_input_tokens': 20}}
    monkeypatch.setattr(translator.urllib.request, 'urlopen', _fake_urlopen({('POST', '/v1/messages'): reply}, seen))
    cfg = {'kind': 'anthropic', 'base': 'https://api.anthropic.com/v1', 'model': 'claude-sonnet-5-5'}
    out, usage = translator.translate(cfg, 'sk-ant-k', {'a': 'Cancel'}, {'pipe': 'أنبوب'})
    assert out == {'a': 'إلغاء'} and usage['requests'] == 1 and usage['input_tokens'] == 120
    assert usage['cached_input_tokens'] == 20
    assert usage['glossary_chars'] == len('{"pipe": "أنبوب"}')
    assert seen[0].get_header('X-api-key') == 'sk-ant-k'
    assert json.loads(json.loads(seen[0].data)['messages'][0]['content'])['glossary'] == {'pipe': 'أنبوب'}


def test_deepl_protects_tokens_and_skips_plural_blocks(monkeypatch):
    seen = []

    def urlopen(req, timeout=None):
        body = json.loads(req.data)
        seen.append(body)
        return _Resp(json.dumps({'translations': [{'text': t.replace('Found', 'وجد'), 'billed_characters': 30}
                                                  for t in body['text']]}).encode())
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    cfg = {'kind': 'deepl', 'base': 'https://api-free.deepl.com/v2', 'model': 'deepl'}
    out, usage = translator.translate(cfg, 'k:fx', {'a': 'Found __1__ [item=pipe] <ok>',
                                                   'p': '__plural_for_parameter__1__{1=pipe|rest=pipes}__'})
    assert out == {'a': 'وجد __1__ [item=pipe] <ok>'} and usage['requests'] == 1 and usage['input_tokens'] == 30
    assert seen[0]['show_billed_characters'] is True
    assert '__1__' not in seen[0]['text'][0] and '<x i="0"/>' in seen[0]['text'][0]


def test_transient_errors_are_retried(monkeypatch):
    calls = {'n': 0}
    monkeypatch.setattr(translator.time, 'sleep', lambda s: None)

    def urlopen(req, timeout=None):
        calls['n'] += 1
        if calls['n'] < 3:
            raise urllib.error.HTTPError(req.full_url, 429, 'slow down', {}, io.BytesIO(b''))
        return _Resp(b'{"data": []}')
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    assert translator.list_models('openai', 'https://x/v1', 'k') == [] and calls['n'] == 3


GEMINI_LISTED = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-3-flash-preview', 'gemini-3.1-flash-lite',
                 'gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-3.8-flash', 'gemini-flash-latest',
                 'gemini-flash-lite-latest', 'gemini-embedding-001', 'gemini-3.5-pro']   # from a real listing, shortened


def test_gemini_ranks_newest_flash_then_lite_fallbacks():
    ranked = translator.pick_models(GEMINI_LISTED, translator.PROVIDERS['gemini'][2])
    assert ranked == ['gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-flash-lite-latest', 'gemini-3.5-pro']
    assert translator.pick_models(['m-3.9', 'm-3.10'], [r'^m-'], 1) == ['m-3.10']   # numbers compare as numbers


def _chat_reply(text):
    return _Resp(json.dumps({'choices': [{'message': {'content': text}}], 'usage': {}}).encode())


def test_an_overloaded_model_hands_over_to_the_next_one(monkeypatch):
    models_sent = []
    monkeypatch.setattr(translator.time, 'sleep', lambda s: None)

    def urlopen(req, timeout=None):
        model = json.loads(req.data)['model']
        models_sent.append(model)
        if model == 'busy':
            body = b'[{"error": {"code": 503, "message": "This model is currently experiencing high demand.", "status": "UNAVAILABLE"}}]'
            raise urllib.error.HTTPError(req.full_url, 503, 'unavailable', {}, io.BytesIO(body))
        return _chat_reply('{"t": {"a": "لوح حديدي"}}')
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    cfg = {'kind': 'openai', 'base': 'https://x/v1', 'model': 'busy', 'fallbacks': ['lite']}
    out, _ = translator.translate(cfg, 'k', {'a': 'Iron plate'})
    assert out == {'a': 'لوح حديدي'} and models_sent == ['busy', 'busy', 'lite']   # 2 tries, then the fallback
    translator.translate(cfg, 'k', {'a': 'Iron plate'})
    assert cfg['model'] == 'lite' and models_sent[-1] == 'lite'                       # later batches keep it


def test_a_silent_model_hands_over_at_once_and_a_lone_one_reports_the_timeout(monkeypatch):
    models_sent = []
    monkeypatch.setattr(translator.time, 'sleep', lambda s: None)

    def urlopen(req, timeout=None):
        models_sent.append(json.loads(req.data)['model'])
        if models_sent[-1] == 'slow':
            raise TimeoutError('The read operation timed out')   # what urllib lets through on a read timeout
        return _chat_reply('{"t": {"a": "مضخة"}}')
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    cfg = {'kind': 'openai', 'base': 'https://x/v1', 'model': 'slow', 'fallbacks': ['lite']}
    assert translator.translate(cfg, 'k', {'a': 'Pump'})[0] == {'a': 'مضخة'} and models_sent == ['slow', 'lite']
    with pytest.raises(translator.TranslatorError, match=r'^timeout: no reply in \d+s$'):   # no crash, no fallback left
        translator.translate({'kind': 'openai', 'base': 'https://x/v1', 'model': 'slow'}, 'k', {'a': 'Pump'})
    assert models_sent[2:] == ['slow'] * 4


def test_the_real_reason_survives_the_retries(monkeypatch):
    monkeypatch.setattr(translator.time, 'sleep', lambda s: None)

    def urlopen(req, timeout=None):
        body = b'[{"error": {"message": "This model is currently experiencing high demand.", "status": "UNAVAILABLE"}}]'
        raise urllib.error.HTTPError(req.full_url, 503, 'unavailable', {}, io.BytesIO(body))
    monkeypatch.setattr(translator.urllib.request, 'urlopen', urlopen)
    with pytest.raises(translator.TranslatorError) as e:
        translator.translate({'kind': 'openai', 'base': 'https://x/v1', 'model': 'm'}, 'k', {'a': 'x'})
    assert e.value.status == 503
    assert str(e.value) == 'HTTP 503 (tried 4 times): This model is currently experiencing high demand.'


def test_a_refused_key_does_not_walk_the_fallbacks(monkeypatch):
    seen = []
    monkeypatch.setattr(translator.urllib.request, 'urlopen', _fake_urlopen({}, seen))   # 401 everywhere
    cfg = {'kind': 'openai', 'base': 'https://x/v1', 'model': 'm', 'fallbacks': ['n', 'o']}
    with pytest.raises(translator.TranslatorError, match='^HTTP 401'):
        translator.translate(cfg, 'k', {'a': 'x'})
    assert len(seen) == 1 and cfg['model'] == 'm' and cfg['fallbacks'] == ['n', 'o']


def test_parse_json_object_tolerates_prose_and_braces_in_strings():
    assert translator.parse_json_object('Here: {"t": {"a": "x } y"}} done') == {'t': {'a': 'x } y'}}
    with pytest.raises(translator.TranslatorError):
        translator.parse_json_object('no json here')
