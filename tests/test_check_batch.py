import json
from tools import check_batch


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8')


def test_reports_count_key_and_token_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(check_batch, 'WORK', tmp_path)
    src = [{'module': 'base', 'key': 'a/x', 'en': 'Press __CONTROL__build__.', 'hint': '', 'reason': 'missing'},
           {'module': 'base', 'key': 'a/y', 'en': 'Iron', 'hint': '', 'reason': 'missing'}]
    _write(tmp_path / 'batches' / '900.jsonl', src)
    (tmp_path / 'batches' / '900.glossary.json').write_text('{}', encoding='utf-8')
    _write(tmp_path / 'out' / '900.jsonl', [{'module': 'base', 'key': 'a/x', 'ar': 'اضغط.'}])
    errs, _ = check_batch.check('900')
    assert any('count' in e for e in errs) and any('tokens' in e for e in errs)


def test_clean_output_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_batch, 'WORK', tmp_path)
    _write(tmp_path / 'batches' / '901.jsonl', [{'module': 'base', 'key': 'a/y', 'en': 'Iron plate', 'hint': '', 'reason': 'missing'}])
    (tmp_path / 'batches' / '901.glossary.json').write_text('{"iron plate": "صفيحة حديد"}', encoding='utf-8')
    _write(tmp_path / 'out' / '901.jsonl', [{'module': 'base', 'key': 'a/y', 'ar': 'صفيحة حديد'}])
    assert check_batch.check('901') == ([], [])


def test_invalid_json_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(check_batch, 'WORK', tmp_path)
    _write(tmp_path / 'batches' / '902.jsonl', [{'module': 'base', 'key': 'a/y', 'en': 'Iron', 'hint': '', 'reason': 'missing'}])
    (tmp_path / 'batches' / '902.glossary.json').write_text('{}', encoding='utf-8')
    (tmp_path / 'out').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'out' / '902.jsonl').write_text('{"module": "base", "key": "a/y", "ar": "حديد\n', encoding='utf-8')
    errs, _ = check_batch.check('902')
    assert errs and 'JSON' in errs[0]
