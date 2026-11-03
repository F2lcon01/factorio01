"""Launch the real game (GUI) in an isolated env with a test mod that screenshots localised strings.
Never touches the user's config, saves or mods: everything lives under %TEMP%\\fa-harness."""
import json, os, re, shutil, subprocess, time
from pathlib import Path
from tools.paths import GAME_EXE, REPORTS

ENV = Path(os.environ['TEMP']) / 'fa-harness'
USER_CFG = Path(os.environ['APPDATA']) / 'Factorio' / 'config' / 'config.ini'
BASE_MODS = ['base', 'elevated-rails', 'quality', 'recycler', 'space-age']

CONTROL_LUA = r'''
local SHOTS = %s
local start, finished_at
local function clear(p)
  if p.gui.screen.fa_frame then p.gui.screen.fa_frame.destroy() end
  p.opened = nil
end
local function show(p, shot)
  clear(p)
  if shot.gui_type then
    p.opened = defines.gui_type[shot.gui_type]
    return
  end
  local f = p.gui.screen.add{type = "frame", name = "fa_frame", direction = "vertical", caption = shot.title}
  f.location = {20, 60}
  for _, row in pairs(shot.rows) do
    local l = f.add{type = "label", caption = row, style = shot.style or "tooltip_label"}
    l.style.single_line = false
  end
end
script.on_event(defines.events.on_tick, function(e)
  local p = game.get_player(1)
  if not p then return end
  if p.controller_type == defines.controllers.cutscene then p.exit_cutscene() end
  start = start or (e.tick + 180)
  if e.tick < start then return end
  local i = math.floor((e.tick - start) / 60) + 1
  local phase = (e.tick - start) %% 60
  local shot = SHOTS[i]
  if shot then
    if phase == 0 then show(p, shot)
    elseif phase == 30 then
      game.take_screenshot{player = p, show_gui = true, path = "fa/" .. shot.name .. ".png", resolution = {1600, 900}}
    end
  elseif not finished_at then
    game.set_wait_for_screenshots_to_finish()
    finished_at = e.tick
  elseif e.tick == finished_at + 60 then
    helpers.write_file("fa-done.txt", "ok")
  end
end)
'''


def to_lua(v):
    if isinstance(v, dict):
        return '{' + ', '.join(f'{k} = {to_lua(x)}' for k, x in v.items()) + '}'
    if isinstance(v, (list, tuple)):
        return '{' + ', '.join(to_lua(x) for x in v) + '}'
    return json.dumps(v, ensure_ascii=False)  # JSON string escapes are valid Lua for our ASCII/UTF-8 content


def _assert_valid_ini(text):
    """Factorio silently ignores a config with duplicate keys and falls back to the user's real data."""
    seen, sec = set(), ''
    for line in text.splitlines():
        s = line.strip()
        if not s or s[0] in ';#':
            continue
        if s.startswith('['):
            sec = s
            continue
        key = (sec, s.split('=', 1)[0])
        if key in seen:
            raise ValueError(f'duplicate config key {key}')
        seen.add(key)
    for need in ('write-data=', 'locale=ar'):
        if need not in text:
            raise ValueError(f'config lacks {need}')


def _kill_ours():
    """Kill only game processes started with our isolated env (never a game the user runs)."""
    # single quotes only: double quotes get mangled crossing the powershell.exe command line
    subprocess.run(['powershell', '-NoProfile', '-Command',
                    "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'factorio.exe' -and "
                    f"$_.CommandLine -like '*{ENV.name}*' }} | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"], check=True)
    for _ in range(20):
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "@(Get-Process factorio -ErrorAction SilentlyContinue).Count"],
                           capture_output=True, text=True)
        if r.stdout.strip() == '0':
            return
        time.sleep(0.5)


def _prepare(shots, locale_cfg, extra_mods):
    if ENV.exists():
        shutil.rmtree(ENV)  # our own temp env only
    for d in ('config', 'mods', 'write'):
        (ENV / d).mkdir(parents=True)
    cfg = USER_CFG.read_text(encoding='utf-8-sig')
    cfg = re.sub(r'(?m)^write-data=.*$', lambda _: f'write-data={ENV / "write"}', cfg)  # path has backslashes
    cfg = re.sub(r'(?m)^locale=.*$', 'locale=ar', cfg)
    cfg = re.sub(r'(?m)^full-screen=.*$', 'full-screen=false', cfg)  # never uncomment ';' lines: duplicates
    _assert_valid_ini(cfg)                                             # make the game ignore the whole file
    (ENV / 'config' / 'config.ini').write_text(cfg, encoding='utf-8')
    mod = ENV / 'mods' / 'fa-harness_0.0.1'
    (mod / 'locale' / 'ar').mkdir(parents=True)
    (mod / 'info.json').write_text(json.dumps({
        'name': 'fa-harness', 'version': '0.0.1', 'title': 'fa-harness', 'author': 'Falcon',
        'factorio_version': '2.1', 'dependencies': ['base >= 2.1.0', '? space-age >= 2.1.0', '? arabic-complete']}),
        encoding='utf-8')
    (mod / 'control.lua').write_text(CONTROL_LUA % to_lua(shots), encoding='utf-8')
    (mod / 'locale' / 'ar' / 'harness.cfg').write_text(locale_cfg, encoding='utf-8')
    names = BASE_MODS + ['fa-harness']
    for m in extra_mods:
        shutil.copytree(m, ENV / 'mods' / Path(m).name)
        names.append(Path(m).name.rsplit('_', 1)[0])
    (ENV / 'mods' / 'mod-list.json').write_text(
        json.dumps({'mods': [{'name': n, 'enabled': True} for n in names]}), encoding='utf-8')


def run(shots, locale_cfg='', extra_mods=(), tag='spike', timeout=300):
    """Returns the list of screenshot paths copied into reports/screens/."""
    _prepare(shots, locale_cfg, extra_mods)
    done = ENV / 'write' / 'script-output' / 'fa-done.txt'
    log_path = ENV / 'write' / 'factorio-current.log'
    # GUI mode re-launches through Steam (steam://run/427520 keeps the arguments), so the
    # Popen'd process exits at once; we track the isolated write dir instead of the process.
    subprocess.Popen([str(GAME_EXE), '-c', str(ENV / 'config' / 'config.ini'),
                      '--mod-directory', str(ENV / 'mods'), '--load-scenario', 'base/freeplay',
                      '--disable-audio', '--window-size', '1600x900'])
    t0 = time.time()
    while not log_path.exists() and time.time() - t0 < 60:
        time.sleep(0.5)
    if not log_path.exists():  # config rejected => the game is writing into the user's real data: stop now
        _kill_ours()
        raise RuntimeError('isolated write-data not used; game killed')
    while not done.exists() and time.time() - t0 < timeout:
        time.sleep(1)
    finished = done.exists()
    _kill_ours()
    log = log_path.read_text(encoding='utf-8', errors='replace')
    if not finished:
        raise RuntimeError('harness did not finish; log tail:\n' + '\n'.join(log.splitlines()[-25:]))
    out = REPORTS / 'screens'
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for png in sorted((ENV / 'write' / 'script-output' / 'fa').glob('*.png')):
        dst = out / f'{tag}-{png.name}'
        shutil.copy(png, dst)
        paths.append(dst)
    return paths
