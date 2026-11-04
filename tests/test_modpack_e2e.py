"""End to end over HTTP: a local OpenAI-compatible provider counts the requests the full build sends."""
import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from tools import modpack
from tools.lint import TOKEN_RE


class _Provider(BaseHTTPRequestHandler):
    posts = []

    def log_message(self, *a):
        pass

    def _reply(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._reply({'data': [{'id': 'text-embedding-x'}, {'id': 'stub-chat'}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        _Provider.posts.append(body)
        strings = json.loads(body['messages'][1]['content'])['strings']
        # Arabic that keeps every placeholder: what a well-behaved model returns
        t = {i: ' '.join(['ترجمة'] + TOKEN_RE.findall(e)) for i, e in strings.items()}
        self._reply({'choices': [{'message': {'content': json.dumps({'t': t}, ensure_ascii=False)}}],
                     'usage': {'prompt_tokens': 30 * len(strings), 'completion_tokens': 10 * len(strings)}})


@pytest.fixture
def provider():
    _Provider.posts = []
    srv = ThreadingHTTPServer(('127.0.0.1', 0), _Provider)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{srv.server_port}/v1'
    srv.shutdown()


def _mod(root, name, version, en_cfg):
    d = root / f'{name}_{version}'
    (d / 'locale' / 'en').mkdir(parents=True)
    (d / 'info.json').write_text(json.dumps({'name': name, 'version': version, 'dependencies': []}))
    (d / 'locale' / 'en' / 'strings.cfg').write_text(en_cfg, encoding='utf-8')


def test_second_build_sends_no_request_and_an_update_sends_only_the_changes(tmp_path, provider, monkeypatch):
    mods = tmp_path / 'mods'
    mods.mkdir()
    (mods / 'mod-list.json').write_text(json.dumps({'mods': [{'name': 'alpha', 'enabled': True},
                                                             {'name': 'beta', 'enabled': True}]}))
    _mod(mods, 'alpha', '1.0.0', '[alpha]\nhello=Hello __1__ pumps\nbye=Goodbye builder\n')
    _mod(mods, 'beta', '1.0.0', '[beta]\nsame=Goodbye builder\nown=Beta only text\n')   # shares a string with alpha
    for k, v in {'FA_MODS_DIR': mods, 'FA_TRANSLATE_KEY': 'stub', 'FA_TRANSLATE_BASE_URL': provider,
                 'FA_OVERRIDES': tmp_path / 'none.json', 'FA_PROGRESS_FILE': tmp_path / 'progress.jsonl'}.items():
        monkeypatch.setenv(k, str(v))
    for k in ('FA_TRANSLATE_PROVIDER', 'FA_TRANSLATE_MODEL'):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(modpack, 'STATE', tmp_path / 'state')
    monkeypatch.setattr(modpack, 'DIST', tmp_path / 'dist')
    monkeypatch.setattr(modpack, 'REPORTS', tmp_path / 'reports')

    first = modpack.build(log=lambda s: None)
    sent = [s for p in _Provider.posts for s in json.loads(p['messages'][1]['content'])['strings'].values()]
    assert first['requests'] >= 1 and first['english_left'] == 0
    assert sorted(sent) == ['Beta only text', 'Goodbye builder', 'Hello __1__ pumps']   # the shared string once
    assert first['translator'] == 'custom / stub-chat'

    n = len(_Provider.posts)
    second = modpack.build(log=lambda s: None)
    assert len(_Provider.posts) == n and second['requests'] == 0 and second['english_left'] == 0
    assert all(s['state'] == 'translated' for s in modpack.status()['states'])

    _mod(mods, 'alpha', '1.1.0', '[alpha]\nhello=Hello __1__ pumps\nbye=Farewell builder\n')   # update upstream
    assert {s['name']: s['state'] for s in modpack.status()['states']}['alpha'] == 'changed'
    third = modpack.build(log=lambda s: None)
    resent = [s for p in _Provider.posts[n:] for s in json.loads(p['messages'][1]['content'])['strings'].values()]
    assert resent == ['Farewell builder'] and third['requests'] == 1

    summary = json.loads((tmp_path / 'state' / 'last_run.json').read_text(encoding='utf-8'))
    assert summary['memory_hits'] >= 3 and summary['tokens_per_string'] == 40.0
    assert (tmp_path / 'dist' / 'arabic-mods-local_1.0.0' / 'locale' / 'ar' / 'alpha.cfg').exists()
    stages = [json.loads(l)['stage'] for l in (tmp_path / 'progress.jsonl').read_text().splitlines()]
    assert stages[0] == 'scan' and stages[-1] == 'done' and 'translate' in stages

    # keep one mod in its original language, then switch it back: no request either way
    pack_ar = tmp_path / 'dist' / 'arabic-mods-local_1.0.0' / 'locale' / 'ar'
    n = len(_Provider.posts)
    assert modpack.status()['changed'] is False
    modpack.keep_original('alpha', True)
    assert modpack.status()['changed'] is True                       # auto-update notices the choice
    kept = modpack.build(log=lambda s: None)
    assert kept['requests'] == 0 and not (pack_ar / 'alpha.cfg').exists() and (pack_ar / 'beta.cfg').exists()
    info = json.loads((tmp_path / 'dist' / 'arabic-mods-local_1.0.0' / 'info.json').read_text(encoding='utf-8'))
    assert '? alpha' not in info['dependencies']
    assert {s['name']: s['state'] for s in modpack.status()['states']} == {'alpha': 'original', 'beta': 'translated'}
    modpack.keep_original('alpha', False)
    assert {s['name']: s['state'] for s in modpack.status()['states']}['alpha'] == 'new'
    back = modpack.build(log=lambda s: None)
    assert back['requests'] == 0 and (pack_ar / 'alpha.cfg').exists() and len(_Provider.posts) == n
