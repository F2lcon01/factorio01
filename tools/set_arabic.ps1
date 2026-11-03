# Switch the game to Arabic and make its name readable in the language list. Waits for Factorio to close first
# (the game rewrites config.ini on exit). Backups go to backups\settings-<stamp>\; -Restore puts them back.
#   powershell -NoProfile -File tools\set_arabic.ps1
#   powershell -NoProfile -File tools\set_arabic.ps1 -Restore
param([int]$WaitMinutes = 30, [switch]$Restore)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cfg = Join-Path $env:APPDATA 'Factorio\config\config.ini'
$info = 'C:\Program Files (x86)\Steam\steamapps\common\Factorio\data\core\locale\ar\info.json'
$utf8 = New-Object Text.UTF8Encoding $false   # both files are UTF-8 without BOM

$t0 = Get-Date
while (Get-Process factorio -ErrorAction SilentlyContinue) {
    if (((Get-Date) - $t0).TotalMinutes -gt $WaitMinutes) { throw 'Factorio is still running' }
    Start-Sleep -Seconds 2
}

if ($Restore) {  # explicit confirmation: a mistaken restore silently switches the game back to English
    $answer = Read-Host 'This returns the game to its previous language. Type YES to continue'
    if ($answer -cne 'YES') { Write-Output 'cancelled: nothing changed'; return }
    $last = Get-ChildItem (Join-Path $root 'backups') -Directory -Filter 'settings-*' | Sort-Object LastWriteTime | Select-Object -Last 1
    Copy-Item (Join-Path $last.FullName 'config.ini') $cfg
    Copy-Item (Join-Path $last.FullName 'core-ar-info.json') $info
    Write-Output "restored from $($last.Name)"
    return
}

$stamp = (Get-Date).ToString('yyyyMMdd-HHmmss', [Globalization.CultureInfo]::InvariantCulture)  # Gregorian, not system calendar
$bk = Join-Path $root "backups\settings-$stamp"
New-Item -ItemType Directory -Force $bk | Out-Null
Copy-Item $cfg (Join-Path $bk 'config.ini')
Copy-Item $info (Join-Path $bk 'core-ar-info.json')

# 1) language = Arabic (only the active, uncommented line)
$text = [IO.File]::ReadAllText($cfg, $utf8)
if (([regex]::Matches($text, '(?m)^locale=')).Count -ne 1) { throw 'expected exactly one active locale= line' }
[IO.File]::WriteAllText($cfg, [regex]::Replace($text, '(?m)^locale=.*$', 'locale=ar'), $utf8)

# 2) readable name in the language list: pre-shaped «العربية» (presentation forms, visual order)
$name = -join ([char[]](0xFE94, 0xFEF4, 0xFE91, 0xFEAE, 0xFECC, 0xFEDF, 0xFE8D))
$json = [IO.File]::ReadAllText($info, $utf8) | ConvertFrom-Json
$json.'language-name' = $name
[IO.File]::WriteAllText($info, ($json | ConvertTo-Json), $utf8)

$check = (Select-String -Path $cfg -Pattern '^locale=').Line
Write-Output "config: $check | language-name set | backup: $bk"
