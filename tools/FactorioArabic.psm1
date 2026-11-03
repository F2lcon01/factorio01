# Shared operations for Change-Language.ps1 (GUI) and tools\auto_update.ps1. Windows PowerShell 5.1 and 7.
# ASCII only on purpose: Windows PowerShell reads BOM-less files as ANSI (user-facing Arabic lives in the GUI file).
#
# Two modes, detected from where this file sits:
#   developer: <project>\tools\FactorioArabic.psm1  -> rebuilds the mod from source with Python (tools\autoupdate.py)
#   player:    <mod>\arabic-tools\FactorioArabic.psm1 -> no Python; repairs from the files shipped in arabic-tools\
$script:UserAppData = $env:APPDATA
$script:ToolsDir = $PSScriptRoot
$script:Root = Split-Path $PSScriptRoot -Parent
$script:Utf8 = New-Object Text.UTF8Encoding $false
$script:ArabicName = -join ([char[]](0xFE94, 0xFEF4, 0xFE91, 0xFEAE, 0xFECC, 0xFEDF, 0xFE8D))  # shaped "Arabic"
$script:ModName = 'arabic-complete'
$script:PortalApi = 'https://mods.factorio.com/api/mods/arabic-complete'

function Set-FAUserAppData([string]$Path) { $script:UserAppData = $Path }   # elevated runs keep the real user's data
function Get-FARoot { $script:Root }
function Test-DevMode { Test-Path (Join-Path $script:Root 'tools\autoupdate.py') }

function Get-FactorioDir {
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

# ---------- scenario / tutorial texts ----------
function Invoke-FAPython([string[]]$PyArgs) {
    Push-Location $script:Root
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # native stderr must not abort Windows PowerShell
    $env:PYTHONIOENCODING = 'utf-8'
    $env:FACTORIO_DATA = Join-Path (Get-FactorioDir) 'data'
    try {
        $out = & python -E @PyArgs 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $old
        Pop-Location
    }
    [pscustomobject]@{ Code = $code; Output = @($out) }
}

function Get-PatchFiles {
    # player mode: arabic-tools\scenario-patch\base\...\locale\<file>.cfg -> game data\base\...\locale\ar\<file>.cfg
    $base = Join-Path $script:ToolsDir 'scenario-patch'
    if (-not (Test-Path $base)) { return @() }
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
        return $done
    }
    $h = Get-FAHealth
    if ($h.Problems -contains 'language-name') { Set-LanguageName; $done += 'fixed-name' }
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
