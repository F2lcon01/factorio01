"""Third-party files for the players' translator bundle (tools.bundle.translator_zip), downloaded once into
work/vendor/ (not tracked) and refused unless their SHA-256 matches the pin published by python.org / PyPI.
python -E -m tools.vendor"""
import hashlib, sys, urllib.request
from tools.paths import WORK

VENDOR = WORK / 'vendor'
FILES = {  # name: (url, sha256 from python.org's release API / PyPI's JSON API)
    'python-3.13.14-embed-amd64.zip': (
        'https://www.python.org/ftp/python/3.13.14/python-3.13.14-embed-amd64.zip',
        '90b4e5b9898b72d744650524bff92377c367f44bd5fbd09e3148656c080ad907'),
    'arabic_reshaper-3.0.1-py3-none-any.whl': (
        'https://files.pythonhosted.org/packages/6e/7d/77752d819ede528c664ecf4de974b17b049e054a14537b74b53c8568014f/'
        'arabic_reshaper-3.0.1-py3-none-any.whl',
        '41c5adc2420f85758eada7e880251c4b6a2adbd83377bd27e5d4eba71f648bc7'),
    'fonttools-4.68.0-py3-none-any.whl': (
        'https://files.pythonhosted.org/packages/35/74/4ea331ecc65ba05a58b1e4e8ccd604c8a15565f876dfbf93fc2a2ea2e22b/'
        'fonttools-4.68.0-py3-none-any.whl',
        'd76f8fdcb6936f5e1045a0c9dd721a4bf11112e60d1e243bfa1d39f06a8b3104'),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def ensure():
    """→ {name: path}; downloads what is missing, verifies everything."""
    VENDOR.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, (url, pin) in FILES.items():
        path = VENDOR / name
        if not path.exists():
            tmp = path.with_suffix('.part')
            urllib.request.urlretrieve(url, tmp)
            tmp.replace(path)
        if sha256(path) != pin:
            raise SystemExit(f'{name}: SHA-256 mismatch, refusing to use it (delete the file to download it again)')
        out[name] = path
    return out


if __name__ == '__main__':
    for n, p in ensure().items():
        print(f'{n}  {p.stat().st_size // 1024} KB  sha256 ok')
