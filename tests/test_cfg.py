from tools.cfg import read_cfg, write_cfg
from tools.paths import GAME_DATA


def test_reads_sections_and_root_keys(tmp_path):
    p = tmp_path / 'a.cfg'
    p.write_text('root=R\n; comment\n[item-name]\niron-plate=Iron plate\n', encoding='utf-8')
    assert read_cfg(p) == {'/root': 'R', 'item-name/iron-plate': 'Iron plate'}


def test_write_follows_given_order_and_skips_missing(tmp_path):
    p = tmp_path / 'b.cfg'
    write_cfg(p, {'s/b': '2', 's/a': '1'}, ['s/a', 's/x', 's/b'])
    assert p.read_text(encoding='utf-8') == '[s]\na=1\nb=2\n'


def test_write_uses_lf_only_like_the_game_files(tmp_path):
    p = tmp_path / 'c.cfg'
    write_cfg(p, {'s/a': '1'}, ['s/a'])
    assert p.read_bytes() == b'[s]\na=1\n'


def test_roundtrip_every_official_locale_file(tmp_path):
    files = list(GAME_DATA.glob('**/locale/en/*.cfg')) + list(GAME_DATA.glob('**/locale/ar/*.cfg'))
    assert files
    for i, src in enumerate(files):
        vals = read_cfg(src)
        out = tmp_path / f'{i}.cfg'
        write_cfg(out, vals, list(vals))
        assert read_cfg(out) == vals, src
