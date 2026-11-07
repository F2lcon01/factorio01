# Shared operations for Change-Language.ps1 (GUI) and tools\auto_update.ps1. Windows PowerShell 5.1 and 7.
# ASCII only on purpose: Windows PowerShell reads BOM-less files as ANSI (user-facing Arabic lives in the GUI file).
#
# Two modes, detected from where this file sits:
#   developer: <project>\tools\FactorioArabic.psm1  -> rebuilds the mod from source with Python (tools\autoupdate.py)
#   player:    arabic-tools\FactorioArabic.psm1 (download/arabic-tools.zip from GitHub) -> no Python; repairs from the
#              scenario-patch shipped inside the installed mod
#   translator bundle (arabic-mods-translator.zip): player mode + python\ (embedded) + app\tools (the Python engine)
$script:UserAppData = $env:APPDATA
$script:ToolsDir = $PSScriptRoot
$script:Root = Split-Path $PSScriptRoot -Parent
$script:Utf8 = New-Object Text.UTF8Encoding $false
$script:ArabicName = -join ([char[]](0xFE94, 0xFEF4, 0xFE91, 0xFEAE, 0xFECC, 0xFEDF, 0xFE8D))  # shaped "Arabic"
$script:ModName = 'arabic-complete'
$script:PortalApi = 'https://mods.factorio.com/api/mods/arabic-complete'
# The language tool and the mods translator ship together (arabic-tools.zip, arabic-mods-translator.zip): one number,
# released as the GitHub tag translator-<version>. The mod keeps its own number, which follows the game's.
$script:ToolsVersion = '1.6.1'
$script:ReleasesApi = 'https://api.github.com/repos/F2lcon01/factorio01/releases?per_page=30'
$script:ReleasesPage = 'https://github.com/F2lcon01/factorio01/releases/latest'
$script:ModPage = 'https://mods.factorio.com/mod/arabic-complete'

function Set-FAUserAppData([string]$Path) { $script:UserAppData = $Path }   # elevated runs keep the real user's data
function Get-FARoot { $script:Root }
function Test-DevMode { Test-Path (Join-Path $script:Root 'tools\autoupdate.py') }

function Get-FactorioDir {
    if ($env:FA_FACTORIO_DIR) { return $env:FA_FACTORIO_DIR }   # tests: a copy of the game's folder layout
    $default = 'C:\Program Files (x86)\Steam\steamapps\common\Factorio'
    if (Test-Path (Join-Path $default 'data\base\info.json')) { return $default }
    $steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue).SteamPath
    if ($steam) {
        $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $dir = Join-Path ($m.Groups[1].Value -replace '\\\\', '\') 'steamapps\common\Factorio'
                if (Test-Path (Join-Path $dir 'data\base\info.json')) { return $dir }
            }
        }
    }
    throw 'Factorio installation not found'
}

function Get-ConfigPath { Join-Path $script:UserAppData 'Factorio\config\config.ini' }
function Get-ModsDir { Join-Path $script:UserAppData 'Factorio\mods' }
function Get-InfoJsonPath { Join-Path (Get-FactorioDir) 'data\core\locale\ar\info.json' }
function Test-GameRunning { [bool](Get-Process factorio -ErrorAction SilentlyContinue) }
function Get-GameVersion { (Get-Content (Join-Path (Get-FactorioDir) 'data\base\info.json') -Raw | ConvertFrom-Json).version }
function Get-MajorMinor([string]$Version) { ($Version.Split('.')[0..1]) -join '.' }

function Get-BackupRoot {
    if (Test-DevMode) { return Join-Path $script:Root 'backups' }
    Join-Path $script:UserAppData 'Factorio\arabic-tools-backup'
}

function Get-GameLanguage {
    $m = Select-String -Path (Get-ConfigPath) -Pattern '^locale=(.*)$'
    if ($m) { return $m.Matches[0].Groups[1].Value.Trim() }
    'auto'
}

function New-SettingsBackup {
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture)
    $dir = Join-Path (Get-BackupRoot) "settings-$stamp"
    New-Item -ItemType Directory -Force $dir | Out-Null
    Copy-Item (Get-ConfigPath) (Join-Path $dir 'config.ini')
    Copy-Item (Get-InfoJsonPath) (Join-Path $dir 'core-ar-info.json')
    $dir
}

function Set-GameLanguage([ValidateSet('ar', 'en')][string]$Code) {
    if (Test-GameRunning) { throw 'GAME_RUNNING' }   # the game rewrites config.ini on exit
    $cfg = Get-ConfigPath
    $text = [IO.File]::ReadAllText($cfg, $script:Utf8)
    if (([regex]::Matches($text, '(?m)^locale=')).Count -ne 1) { throw 'expected exactly one active locale= line' }
    [IO.File]::WriteAllText($cfg, [regex]::Replace($text, '(?m)^locale=.*$', "locale=$Code"), $script:Utf8)
}

function Test-LanguageNamePatched {
    ([IO.File]::ReadAllText((Get-InfoJsonPath), $script:Utf8) | ConvertFrom-Json).'language-name' -eq $script:ArabicName
}

function Set-LanguageName {
    $p = Get-InfoJsonPath
    $j = [IO.File]::ReadAllText($p, $script:Utf8) | ConvertFrom-Json
    $j.'language-name' = $script:ArabicName
    [IO.File]::WriteAllText($p, ($j | ConvertTo-Json), $script:Utf8)
}

# ---------- installed mod (folder from our installer, or zip from the mod portal) ----------
function Get-ModInfo {
    $mods = Get-ModsDir
    $dir = Get-ChildItem $mods -Directory -Filter "$($script:ModName)_*" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($dir) {
        $j = Get-Content (Join-Path $dir.FullName 'info.json') -Raw | ConvertFrom-Json
        return [pscustomobject]@{ Version = $j.version; FactorioVersion = $j.factorio_version; Path = $dir.FullName }
    }
    $zip = Get-ChildItem $mods -File -Filter "$($script:ModName)_*.zip" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($zip) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $z = [IO.Compression.ZipFile]::OpenRead($zip.FullName)
        try {
            $e = $z.Entries | Where-Object { $_.FullName -match '^[^/]+/info\.json$' } | Select-Object -First 1
            $r = New-Object IO.StreamReader($e.Open())
            $j = $r.ReadToEnd() | ConvertFrom-Json
            $r.Close()
        } finally { $z.Dispose() }
        return [pscustomobject]@{ Version = $j.version; FactorioVersion = $j.factorio_version; Path = $zip.FullName }
    }
    $null
}

function Get-InstalledModVersion { $m = Get-ModInfo; if ($m) { return $m.Version }; $null }

function Get-ModListPath { Join-Path (Get-ModsDir) 'mod-list.json' }

function Test-ModEnabled {
    $m = (Get-Content (Get-ModListPath) -Raw | ConvertFrom-Json).mods | Where-Object { $_.name -eq $script:ModName }
    [bool]($m -and $m.enabled)
}

function Enable-Mod {
    $p = Get-ModListPath
    $data = Get-Content $p -Raw | ConvertFrom-Json
    $data.mods = @($data.mods | Where-Object { $_.name -ne $script:ModName }) + [pscustomobject]@{ name = $script:ModName; enabled = $true }
    [IO.File]::WriteAllText($p, ($data | ConvertTo-Json -Depth 5), $script:Utf8)
}

function Get-PortalRelease {
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $r = Invoke-RestMethod -Uri $script:PortalApi -TimeoutSec 10
        $rel = $r.releases | Sort-Object { [version]$_.version } | Select-Object -Last 1
        return [pscustomobject]@{ Version = $rel.version; FactorioVersion = $rel.info_json.factorio_version }
    } catch { return $null }
}

# ---------- versions: this tool, the mod, and what is newest online ----------
function Get-FAToolsVersion { $script:ToolsVersion }
function Get-FAReleasesPage { $script:ReleasesPage }
function Get-FAModPage { $script:ModPage }

# Windows shapes digits by context in right-to-left controls (47 -> Arabic-Indic, 2.2.6 reversed). The project rule is
# Western digits: wrap numbers in a left-to-right embedding that starts with a left-to-right mark.
function N($Value) { [string][char]0x202A + [char]0x200E + "$Value" + [char]0x202C }

function Read-FAToolsRelease($Releases) {
    # GitHub's release list -> the newest translator-<x.y.z> that is neither a draft nor a pre-release, or $null
    $best = $null
    foreach ($r in @($Releases)) {
        if ($r.draft -or $r.prerelease -or "$($r.tag_name)" -notmatch '^translator-(\d+\.\d+\.\d+)$') { continue }
        $v = $Matches[1]
        if (-not $best -or [version]$v -gt [version]$best.Version) { $best = [pscustomobject]@{ Version = $v; Url = $r.html_url } }
    }
    $best
}

function Read-FAModRelease($Portal) {
    # the mod portal's answer -> its newest release, or $null
    $rel = @($Portal.releases) | Where-Object { $_.version } | Sort-Object { [version]$_.version } | Select-Object -Last 1
    if (-not $rel) { return $null }
    [pscustomobject]@{ Version = $rel.version; FactorioVersion = $rel.info_json.factorio_version }
}

function Start-FAUpdateCheck {
    # Two GETs that do not block a window: GitHub releases (this tool) and the mod portal (the mod). Poll with
    # Get-FAUpdateResult from a WinForms timer. Nothing about the user is sent.
    Add-Type -AssemblyName System.Net.Http
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $client = New-Object Net.Http.HttpClient
    $client.Timeout = [TimeSpan]::FromSeconds(10)
    $client.DefaultRequestHeaders.UserAgent.ParseAdd('factorio-arabic-tools/' + $script:ToolsVersion)
    @{ Client = $client; Tools = $client.GetStringAsync($script:ReleasesApi); Mod = $client.GetStringAsync($script:PortalApi) }
}

function Get-FAUpdateResult($Check) {
    # $null while a request is still running. Then: Tools/Mod = @{ Current; Latest ($null: unreachable); Newer }
    if (-not ($Check.Tools.IsCompleted -and $Check.Mod.IsCompleted)) { return $null }
    $tools = $null; $mod = $null
    try { if ($Check.Tools.Status -eq 'RanToCompletion') { $tools = Read-FAToolsRelease ($Check.Tools.Result | ConvertFrom-Json) } } catch { }
    try { if ($Check.Mod.Status -eq 'RanToCompletion') { $mod = Read-FAModRelease ($Check.Mod.Result | ConvertFrom-Json) } } catch { }
    $Check.Client.Dispose()
    $installed = Get-InstalledModVersion
    [pscustomobject]@{
        Tools = [pscustomobject]@{ Current = $script:ToolsVersion; Latest = $(if ($tools) { $tools.Version } else { $null })
                                   Url = $(if ($tools) { $tools.Url } else { $script:ReleasesPage })
                                   Newer = [bool]($tools -and [version]$tools.Version -gt [version]$script:ToolsVersion) }
        Mod = [pscustomobject]@{ Current = $installed; Latest = $(if ($mod) { $mod.Version } else { $null }); Url = $script:ModPage
                                 Newer = [bool]($mod -and $installed -and [version]$mod.Version -gt [version]$installed) }
    }
}

# ---------- Python: the project's own, or the embedded one shipped in arabic-mods-translator.zip ----------
function Test-EmbeddedPython { Test-Path (Join-Path $script:ToolsDir 'python\python.exe') }

function Get-FAPython {
    # -> @{ Exe; Args (before -m); Cwd }. Embedded: python\python313._pth puts ..\app on sys.path.
    if (Test-EmbeddedPython) {
        return @{ Exe = (Join-Path $script:ToolsDir 'python\python.exe'); Args = @('-E', '-s'); Cwd = (Join-Path $script:ToolsDir 'app') }
    }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw 'Python not found' }
    @{ Exe = $py.Source; Args = @('-E'); Cwd = $script:Root }
}

function Get-FAStateDir {
    # memory, manifest, usage: in the project for the developer; in the user's profile for players (survives updates)
    if (Test-DevMode) { return Join-Path $script:Root 'work\modpack' }
    Join-Path $script:UserAppData 'Factorio\arabic-tools\translator'
}

function Set-FAPythonEnv {
    $env:PYTHONIOENCODING = 'utf-8'
    $env:FACTORIO_DATA = Join-Path (Get-FactorioDir) 'data'
    $env:FA_MODS_DIR = Get-ModsDir
    $env:FA_STATE_DIR = Get-FAStateDir
}

function Invoke-FAPython([string[]]$PyArgs) {
    $py = Get-FAPython
    Push-Location $py.Cwd
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # native stderr must not abort Windows PowerShell
    Set-FAPythonEnv
    # Python writes UTF-8 (PYTHONIOENCODING); PowerShell decodes a native program's output with the console code page,
    # which is the OEM one (720 on Arabic Windows) when started from Explorer: Arabic would arrive garbled.
    $enc = $null
    try { $enc = [Console]::OutputEncoding; [Console]::OutputEncoding = New-Object Text.UTF8Encoding $false } catch { }
    try {
        $all = @($py.Args) + @($PyArgs)
        $out = & $py.Exe @all 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
    } finally {
        if ($enc) { try { [Console]::OutputEncoding = $enc } catch { } }
        $ErrorActionPreference = $old
        Pop-Location
    }
    [pscustomobject]@{ Code = $code; Output = @($out) }
}

function Start-FAPython([string[]]$PyArgs, [string]$StdOut, [string]$StdErr) {
    # Background run for the window: output goes to files the window polls; the child inherits $env (key included).
    $py = Get-FAPython
    Set-FAPythonEnv
    $quoted = (@($py.Args) + @($PyArgs)) | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }
    $p = Start-Process -FilePath $py.Exe -ArgumentList ($quoted -join ' ') -WorkingDirectory $py.Cwd -WindowStyle Hidden `
        -RedirectStandardOutput $StdOut -RedirectStandardError $StdErr -PassThru
    # Start-Process does not keep the process handle: once the child exits, ExitCode reads as $null (success and
    # failure alike), and the window took every run for a failure. Opening the handle now keeps the exit code.
    $null = $p.Handle
    $p
}

# ---------- the translator's API key: DPAPI, this Windows user only, never in the project ----------
function Get-FAKeyFile { Join-Path $script:UserAppData 'Factorio\arabic-tools\translator-key.txt' }

function Get-FATranslatorKey {
    $f = Get-FAKeyFile
    if (-not (Test-Path $f)) { return '' }
    try { [Net.NetworkCredential]::new('', (Get-Content $f -Raw | ConvertTo-SecureString)).Password } catch { '' }
}

function Save-FATranslatorKey([securestring]$Key) {
    $f = Get-FAKeyFile
    New-Item -ItemType Directory -Force (Split-Path $f -Parent) | Out-Null
    [IO.File]::WriteAllText($f, ($Key | ConvertFrom-SecureString))
    $f
}

function Get-FAProviderFile { Join-Path $script:UserAppData 'Factorio\arabic-tools\translator-provider.json' }
function Test-FAProviderChoice { Test-Path (Get-FAProviderFile) }   # $false: first run, the window suggests Gemini

function Get-FAProviderChoice {
    # the provider the user picked in the window (not secret): @{ provider = ''|'openai'|...|'custom'; base_url = '' }
    $f = Get-FAProviderFile
    if (Test-Path $f) { try { return (Get-Content $f -Raw | ConvertFrom-Json) } catch { } }
    [pscustomobject]@{ provider = ''; base_url = '' }
}

function Save-FAProviderChoice([string]$Provider, [string]$BaseUrl) {
    $f = Get-FAProviderFile
    New-Item -ItemType Directory -Force (Split-Path $f -Parent) | Out-Null
    [IO.File]::WriteAllText($f, (@{ provider = $Provider; base_url = $BaseUrl } | ConvertTo-Json), $script:Utf8)
}

function Remove-FATranslatorKey {
    $f = Get-FAKeyFile
    if (Test-Path $f) { [IO.File]::Delete($f); return $true }   # our own file, removed on the user's request
    $false
}

# ---------- a generated pack (arabic-mods-local): install / roll back, nothing deleted ----------
function Install-FAPack([string]$Path) {
    if (Test-GameRunning) { throw 'GAME_RUNNING' }
    $leaf = Split-Path $Path -Leaf
    $name = $leaf -replace '_\d+\.\d+\.\d+$', ''
    Uninstall-FAPack $name -Enable | Out-Null
    Copy-Item $Path (Join-Path (Get-ModsDir) $leaf) -Recurse
    "installed $leaf"
}

function Uninstall-FAPack([string]$Name, [switch]$Enable) {
    # Parks every installed copy in mods-parked (outside mods\) and sets the mod-list entry; -Enable when reinstalling.
    if (Test-GameRunning) { throw 'GAME_RUNNING' }
    $mods = Get-ModsDir
    $parked = Join-Path (Split-Path $mods -Parent) 'mods-parked'
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture)
    New-Item -ItemType Directory -Force $parked | Out-Null
    $list = Get-ModListPath
    Copy-Item $list (Join-Path $parked "mod-list.json.bak-$stamp")
    Get-ChildItem $mods -Directory -Filter "${Name}_*" | ForEach-Object { Move-Item $_.FullName (Join-Path $parked "$($_.Name)-$stamp") }
    $data = Get-Content $list -Raw | ConvertFrom-Json
    $data.mods = @($data.mods | Where-Object { $_.name -ne $Name }) + [pscustomobject]@{ name = $Name; enabled = [bool]$Enable }
    [IO.File]::WriteAllText($list, ($data | ConvertTo-Json -Depth 5), $script:Utf8)
    "parked $Name in $parked"
}

function Get-PatchDir {
    # player mode: the patch ships inside the installed mod (<mod>\scenario-patch), so it always matches the mod version;
    # the mod portal rejects scripts, so this tool itself comes from GitHub
    $local = Join-Path $script:ToolsDir 'scenario-patch'
    if (Test-Path $local) { return $local }
    $mod = Get-ModInfo
    if (-not $mod) { return $null }
    if (Test-Path $mod.Path -PathType Container) {
        $d = Join-Path $mod.Path 'scenario-patch'
        if (Test-Path $d) { return $d }
        return $null
    }
    $cache = Join-Path (Get-BackupRoot) ('patch-' + $mod.Version)   # zip from the mod portal: extract once per mod version
    if (-not (Test-Path (Join-Path $cache 'complete.txt'))) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $z = [IO.Compression.ZipFile]::OpenRead($mod.Path)
        try {
            $n = 0
            foreach ($e in $z.Entries) {
                if ($e.FullName -notmatch '^[^/]+/scenario-patch/(.+\.cfg)$') { continue }
                $dest = Join-Path $cache ($Matches[1] -replace '/', '\')
                New-Item -ItemType Directory -Force (Split-Path $dest -Parent) | Out-Null
                [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $dest, $true)
                $n++
            }
        } finally { $z.Dispose() }
        if (-not $n) { return $null }   # an older release without the patch
        [IO.File]::WriteAllText((Join-Path $cache 'complete.txt'), "$n")
    }
    $cache
}

function Get-PatchFiles {
    # scenario-patch\base\...\locale\<file>.cfg -> game data\base\...\locale\ar\<file>.cfg
    $base = Get-PatchDir
    if (-not $base) { return @() }
    $data = Join-Path (Get-FactorioDir) 'data'
    Get-ChildItem $base -Recurse -Filter '*.cfg' | ForEach-Object {
        $rel = $_.FullName.Substring($base.Length + 1)
        [pscustomobject]@{ Patch = $_.FullName; Rel = $rel; Game = Join-Path $data ((Split-Path $rel -Parent) + '\ar\' + $_.Name) }
    }
}

function Test-SameFile([string]$A, [string]$B) {
    (Test-Path $A) -and (Test-Path $B) -and ((Get-FileHash $A).Hash -eq (Get-FileHash $B).Hash)
}

function Get-ScenarioState {
    if (Test-DevMode) {
        $r = Invoke-FAPython @('-m', 'tools.scenarios', 'status')
        $line = ($r.Output | Select-Object -Last 1)
        if ($r.Code -ne 0 -or $line -notmatch "'patched': (\d+), 'original': (\d+), 'other': (\d+)") { return $null }
        return [pscustomobject]@{ Patched = [int]$Matches[1]; Original = [int]$Matches[2]; Other = [int]$Matches[3] }
    }
    $files = @(Get-PatchFiles)
    if (-not $files.Count) { return $null }
    $patched = @($files | Where-Object { Test-SameFile $_.Game $_.Patch }).Count
    [pscustomobject]@{ Patched = $patched; Original = $files.Count - $patched; Other = 0 }
}

function Test-ScenariosPatched {
    $s = Get-ScenarioState
    [bool]($s -and $s.Original -eq 0 -and $s.Other -eq 0)
}

function Repair-Scenarios {
    if (Test-DevMode) {   # after a Steam update the game files are new originals: rebuild and re-apply
        $b = Invoke-FAPython @('-m', 'tools.scenarios', 'build', '--allow-missing')
        if ($b.Code -ne 0) { throw "scenario build failed: $($b.Output -join ' ')" }
        $a = Invoke-FAPython @('-m', 'tools.scenarios', 'apply')
        if ($a.Code -ne 0) { throw "scenario apply failed: $($a.Output -join ' ')" }
        return Get-ScenarioState
    }
    $backup = Join-Path (Get-BackupRoot) ('scenarios-' + (Get-GameVersion))   # pristine originals, once per game version
    foreach ($f in Get-PatchFiles) {
        if (Test-SameFile $f.Game $f.Patch) { continue }
        $b = Join-Path $backup $f.Rel
        if ((Test-Path $f.Game) -and -not (Test-Path $b)) {
            New-Item -ItemType Directory -Force (Split-Path $b -Parent) | Out-Null
            Copy-Item $f.Game $b
        }
        Copy-Item $f.Patch $f.Game -Force
    }
    Get-ScenarioState
}

# ---------- the game's own core texts: what it shows before any mod is loaded ----------
# Screens such as "Error loading mods" appear before mods load, so they read data\core\locale\ar\core.cfg: the
# game's Crowdin Arabic, typed in reversed letter order and unshaped, which the engine shows as reversed, broken
# words. The installed mod's core.cfg (shaped, ordered for the engine) is copied over it; the original is kept
# once per game version, and Steam's "verify integrity of game files" brings it back.
function Get-GameCoreCfg { Join-Path (Get-FactorioDir) 'data\core\locale\ar\core.cfg' }

function Get-ModCoreCfg {
    $mod = Get-ModInfo
    if (-not $mod) { return $null }
    if (Test-Path $mod.Path -PathType Container) {
        $f = Join-Path $mod.Path 'locale\ar\core.cfg'
        if (Test-Path $f) { return $f }
        return $null
    }
    $f = Join-Path (Get-BackupRoot) ('core-' + $mod.Version + '\core.cfg')   # zip from the mod portal: extract once
    if (-not (Test-Path $f)) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $z = [IO.Compression.ZipFile]::OpenRead($mod.Path)
        try {
            $e = $z.Entries | Where-Object { $_.FullName -match '^[^/]+/locale/ar/core\.cfg$' } | Select-Object -First 1
            if (-not $e) { return $null }
            New-Item -ItemType Directory -Force (Split-Path $f -Parent) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $f, $true)
        } finally { $z.Dispose() }
    }
    $f
}

function Test-CoreLocalePatched {
    $src = Get-ModCoreCfg
    (-not $src) -or (Test-SameFile (Get-GameCoreCfg) $src)   # no mod core.cfg: nothing to compare with
}

function Repair-CoreLocale {
    $src = Get-ModCoreCfg
    if (-not $src) { return $false }
    $game = Get-GameCoreCfg
    if (Test-SameFile $game $src) { return $true }
    $backup = Join-Path (Get-BackupRoot) ('core-original-' + (Get-GameVersion) + '\core.cfg')
    if ((Test-Path $game) -and -not (Test-Path $backup)) {
        New-Item -ItemType Directory -Force (Split-Path $backup -Parent) | Out-Null
        Copy-Item $game $backup
    }
    New-Item -ItemType Directory -Force (Split-Path $game -Parent) | Out-Null
    Copy-Item $src $game -Force
    $true
}

# ---------- health check and one-click fix ----------
function Get-FAHealth {
    $game = Get-GameVersion
    $mod = Get-ModInfo
    $problems = @()
    if (-not $mod) { $problems += 'mod-missing' }
    else {
        if ($mod.Version -ne $game) { $problems += 'version-mismatch' }
        if ($mod.FactorioVersion -ne (Get-MajorMinor $game)) { $problems += 'incompatible' }
        if (-not (Test-ModEnabled)) { $problems += 'mod-disabled' }
    }
    if ((Get-GameLanguage) -eq 'ar') {
        if (-not (Test-LanguageNamePatched)) { $problems += 'language-name' }
        if ($mod -and -not (Test-CoreLocalePatched)) { $problems += 'core-locale' }
        $s = Get-ScenarioState
        if ($s -and ($s.Original -gt 0 -or $s.Other -gt 0)) { $problems += 'scenarios' }
    }
    [pscustomobject]@{
        GameVersion = $game
        ModVersion = $(if ($mod) { $mod.Version } else { $null })
        Mode = $(if (Test-DevMode) { 'developer' } else { 'player' })
        Problems = $problems
    }
}

function Invoke-FAFix {
    # returns result codes; the GUI turns them into Arabic sentences
    if (Test-GameRunning) { throw 'GAME_RUNNING' }
    $done = @()
    if (Test-DevMode) {
        & (Join-Path $script:ToolsDir 'auto_update.ps1') -Force | Out-Null   # rebuild the mod to the game version + repairs
        $done += 'rebuilt'
        if ((Get-GameLanguage) -eq 'ar' -and -not (Test-LanguageNamePatched)) { Set-LanguageName; $done += 'fixed-name' }
        if ((Get-GameLanguage) -eq 'ar' -and -not (Test-CoreLocalePatched)) { if (Repair-CoreLocale) { $done += 'fixed-core' } }
        return $done
    }
    $h = Get-FAHealth
    if ($h.Problems -contains 'language-name') { Set-LanguageName; $done += 'fixed-name' }
    if ($h.Problems -contains 'core-locale') { if (Repair-CoreLocale) { $done += 'fixed-core' } }
    if ($h.Problems -contains 'scenarios') { [void](Repair-Scenarios); $done += 'fixed-scenarios' }
    if ($h.Problems -contains 'mod-disabled') { Enable-Mod; $done += 'enabled-mod' }
    if ($h.Problems -contains 'version-mismatch' -or $h.Problems -contains 'incompatible' -or $h.Problems -contains 'mod-missing') {
        $rel = Get-PortalRelease
        $game = $h.GameVersion
        if (-not $rel) { $done += 'portal-unreachable' }
        elseif (-not $h.ModVersion) { $done += "install-available:$($rel.Version)" }
        elseif ([version]$rel.Version -gt [version]$h.ModVersion) { $done += "update-available:$($rel.Version)" }
        elseif ($rel.FactorioVersion -eq (Get-MajorMinor $game)) { $done += 'compatible-latest' }
        else { $done += 'wait-for-update' }
    }
    $done
}

Export-ModuleMember -Function *
