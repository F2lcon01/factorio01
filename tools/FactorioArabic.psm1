# Shared operations for Change-Language.ps1 (GUI) and tools\auto_update.ps1. Windows PowerShell 5.1 and 7.
# ASCII only on purpose: Windows PowerShell reads BOM-less files as ANSI.
$script:UserAppData = $env:APPDATA
$script:Root = Split-Path $PSScriptRoot -Parent
$script:Utf8 = New-Object Text.UTF8Encoding $false
$script:ArabicName = -join ([char[]](0xFE94, 0xFEF4, 0xFE91, 0xFEAE, 0xFECC, 0xFEDF, 0xFE8D))  # shaped "Arabic"
$script:ModName = 'arabic-complete'

function Set-FAUserAppData([string]$Path) { $script:UserAppData = $Path }   # elevated runs keep the real user's data
function Get-FARoot { $script:Root }

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

function Get-GameLanguage {
    $m = Select-String -Path (Get-ConfigPath) -Pattern '^locale=(.*)$'
    if ($m) { return $m.Matches[0].Groups[1].Value.Trim() }
    'auto'
}

function New-SettingsBackup {
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture)
    $dir = Join-Path $script:Root "backups\settings-$stamp"
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

function Get-InstalledModVersion {
    $d = Get-ChildItem (Get-ModsDir) -Directory -Filter "$($script:ModName)_*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($d) { return $d.Name.Substring($script:ModName.Length + 1) }
    $null
}

function Test-ModEnabled {
    $m = (Get-Content (Join-Path (Get-ModsDir) 'mod-list.json') -Raw | ConvertFrom-Json).mods |
        Where-Object { $_.name -eq $script:ModName }
    [bool]($m -and $m.enabled)
}

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

function Get-ScenarioState {
    $r = Invoke-FAPython @('-m', 'tools.scenarios', 'status')
    $line = ($r.Output | Select-Object -Last 1)
    if ($r.Code -ne 0 -or $line -notmatch "'patched': (\d+), 'original': (\d+), 'other': (\d+)") { return $null }
    [pscustomobject]@{ Patched = [int]$Matches[1]; Original = [int]$Matches[2]; Other = [int]$Matches[3] }
}

function Test-ScenariosPatched {
    $s = Get-ScenarioState
    [bool]($s -and $s.Original -eq 0 -and $s.Other -eq 0)
}

function Repair-Scenarios {
    # after a Steam update the game files are new originals: rebuild (taking new keys from the game) and re-apply
    $b = Invoke-FAPython @('-m', 'tools.scenarios', 'build', '--allow-missing')
    if ($b.Code -ne 0) { throw "scenario build failed: $($b.Output -join ' ')" }
    $a = Invoke-FAPython @('-m', 'tools.scenarios', 'apply')
    if ($a.Code -ne 0) { throw "scenario apply failed: $($a.Output -join ' ')" }
    Get-ScenarioState
}

Export-ModuleMember -Function *
