# Install / uninstall the built mod into the user's Factorio mods folder. Never deletes: old copies are parked.
# PowerShell, not Python: the Microsoft Store Python virtualizes writes under %APPDATA% (they land in its private
# LocalCache and the game never sees them) — verified 2026-11-03.
#   powershell -File tools\install.ps1 -Version 1.0.0
#   powershell -File tools\install.ps1 -Uninstall
#   powershell -File tools\install.ps1 -Name arabic-mods-local -Version 1.0.0   # the pack from tools\translate_mods.ps1
param([string]$Version, [switch]$Uninstall, [string]$Name = 'arabic-complete')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$factorio = Join-Path $env:APPDATA 'Factorio'
$mods = Join-Path $factorio 'mods'
$parked = Join-Path $factorio 'mods-parked'   # outside mods\: the game would try to load any folder inside it
$list = Join-Path $mods 'mod-list.json'
$name = $Name
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

if (Get-Process factorio -ErrorAction SilentlyContinue) { throw 'Factorio is running; close it first.' }
if (-not $Uninstall -and -not $Version) { throw 'pass -Version x.y.z or -Uninstall' }
New-Item -ItemType Directory -Force $parked | Out-Null
Copy-Item $list (Join-Path $parked "mod-list.json.bak-$stamp")
Get-ChildItem $mods -Directory -Filter "${name}_*" | ForEach-Object {
    Move-Item $_.FullName (Join-Path $parked "$($_.Name)-$stamp")
}
if (-not $Uninstall) {
    $src = Join-Path $root "dist\${name}_$Version"
    if (-not (Test-Path $src)) { throw "build first: python -E -m tools.build $Version" }
    Copy-Item $src (Join-Path $mods "${name}_$Version") -Recurse
}
$data = Get-Content $list -Raw | ConvertFrom-Json
$data.mods = @($data.mods | Where-Object { $_.name -ne $name }) + [pscustomobject]@{ name = $name; enabled = (-not $Uninstall) }
[IO.File]::WriteAllText($list, ($data | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))  # no BOM; PS 5.1 + 7

$state = if ($Uninstall) { 'disabled; folders parked in ' + $parked } else { "installed ${name}_$Version" }
Write-Output $state
