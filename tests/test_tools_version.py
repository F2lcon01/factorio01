"""One version number for both tool zips, and the update check's reading of GitHub and the mod portal.
Runs the real module in Windows PowerShell 5.1 (what players have)."""
import json, re, shutil, subprocess
import pytest
from tools import bundle
from tools.paths import ROOT

PS = shutil.which('powershell')
pytestmark = pytest.mark.skipif(not PS, reason='Windows PowerShell not found')
MODULE = ROOT / 'tools' / 'FactorioArabic.psm1'


def _ps(script):
    cmd = f"$ErrorActionPreference = 'Stop'; Import-Module '{MODULE}' -Force; {script}"
    r = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def _read(tmp_path, function, data):
    f = tmp_path / 'answer.json'
    f.write_text(json.dumps(data), encoding='utf-8')
    return json.loads(_ps(f"{function} (Get-Content '{f}' -Raw | ConvertFrom-Json) | ConvertTo-Json -Compress") or 'null')


def test_one_version_for_both_tools_and_the_release_tag():
    v = bundle.tools_version()
    assert re.fullmatch(r'\d+\.\d+\.\d+', v)
    assert _ps('Get-FAToolsVersion') == v
    for name in ('Change-Language.ps1', 'Translate-Mods.ps1'):   # both windows show it in the title and the version line
        assert (ROOT / name).read_text(encoding='utf-8-sig').count('Get-FAToolsVersion') >= 2, name


def test_newest_tools_release_skips_drafts_prereleases_and_mod_tags(tmp_path):
    releases = [{'tag_name': 'v2.1.24', 'html_url': 'u-mod'},
                {'tag_name': 'translator-1.1.1', 'html_url': 'u-111'},
                {'tag_name': 'translator-1.10.0', 'html_url': 'u-1100'},   # numbers, not text: 1.10 > 1.9
                {'tag_name': 'translator-1.9.0', 'html_url': 'u-190'},
                {'tag_name': 'translator-3.0.0', 'html_url': 'u-pre', 'prerelease': True},
                {'tag_name': 'translator-4.0.0', 'html_url': 'u-draft', 'draft': True}]
    assert _read(tmp_path, 'Read-FAToolsRelease', releases) == {'Version': '1.10.0', 'Url': 'u-1100'}
    assert _read(tmp_path, 'Read-FAToolsRelease', releases[:1]) is None


def test_newest_mod_release_from_the_portal(tmp_path):
    portal = {'releases': [{'version': '2.1.24', 'info_json': {'factorio_version': '2.1'}},
                           {'version': '2.1.9', 'info_json': {'factorio_version': '2.1'}}]}
    assert _read(tmp_path, 'Read-FAModRelease', portal) == {'Version': '2.1.24', 'FactorioVersion': '2.1'}


def test_a_background_run_reports_its_real_exit_code():
    # the window decides success from ExitCode: Start-Process alone reads $null after exit, so every key check and
    # every build looked failed (translator 1.0.0 to 1.2.0)
    script = ("$d = Join-Path $env:TEMP 'fa-exitcode'; New-Item -ItemType Directory -Force $d | Out-Null; "
              "foreach ($c in @('print(1)', 'import sys; sys.exit(3)')) { "
              "$p = Start-FAPython @('-c', $c) (Join-Path $d 'o.txt') (Join-Path $d 'e.txt'); "
              "while (-not $p.HasExited) { Start-Sleep -Milliseconds 50 }; $p.WaitForExit(); "
              "if ($null -eq $p.ExitCode) { 'null' } else { $p.ExitCode } }")
    try:
        assert _ps(script).split() == ['0', '3']
    except AssertionError as e:
        if 'Factorio installation not found' in str(e):
            pytest.skip('needs a Factorio installation (Set-FAPythonEnv)')
        raise


def test_an_unreachable_check_reports_nothing_newer():
    # a closed local port: both requests fail fast, and the result says "unknown", never "newer"
    out = _ps("$c = Start-FAUpdateCheck; $c.Tools = $c.Client.GetStringAsync('http://127.0.0.1:9/'); "
              "$c.Mod = $c.Client.GetStringAsync('http://127.0.0.1:9/'); $d = (Get-Date).AddSeconds(20); "
              "while (-not ($r = Get-FAUpdateResult $c) -and (Get-Date) -lt $d) { Start-Sleep -Milliseconds 100 }; "
              "$r | ConvertTo-Json -Compress -Depth 3")
    r = json.loads(out)
    assert r['Tools']['Latest'] is None and r['Tools']['Newer'] is False and r['Mod']['Newer'] is False
