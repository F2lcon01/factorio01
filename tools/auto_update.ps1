# Smart auto-update: follows the installed game version, repairs what Steam restores, and rebuilds the Arabic
# pack for other installed mods when they change.
#   powershell -NoProfile -File tools\auto_update.ps1            # run now (quick when nothing changed)
#   powershell -NoProfile -File tools\auto_update.ps1 -Force     # rebuild and reinstall even if versions match
#   powershell -NoProfile -File tools\auto_update.ps1 -Register  # run automatically: at logon and every 6 hours
#   powershell -NoProfile -File tools\auto_update.ps1 -Unregister
# Log: reports\auto-update.log  |  details of new strings: reports\auto-update.md
# Windows PowerShell 5.1 and 7. ASCII only (see FactorioArabic.psm1).
param([switch]$Force, [switch]$Register, [switch]$Unregister)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'FactorioArabic.psm1') -Force
$root = Get-FARoot
$log = Join-Path $root 'reports\auto-update.log'
$stateFile = Join-Path $root 'work\state.json'
$taskName = 'Factorio Arabic Auto-Update'

function Log([string]$Message) {
    $line = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture) + '  ' + $Message
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Output $line
}

if ($Register) {
    $ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $action = New-ScheduledTaskAction -Execute $ps -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"')
    $atLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $every6h = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 6)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($atLogon, $every6h) -Settings $settings `
        -Description 'Keeps the Arabic Factorio mod in step with the installed game version.' -Force | Out-Null
    Log "registered scheduled task '$taskName' (at logon + every 6 hours)"
    return
}
if ($Unregister) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Log "unregistered scheduled task '$taskName'"
    return
}

if (Test-GameRunning) { Log 'skipped: the game is running (next trigger will retry)'; return }

$version = Get-GameVersion
$state = $null
if (Test-Path $stateFile) { $state = Get-Content $stateFile -Raw | ConvertFrom-Json }
$installed = Get-InstalledModVersion
$changed = $Force -or -not $state -or $state.game_version -ne $version -or $installed -ne $version

if ($changed) {
    Log "game $version (last seen: $(if ($state) { $state.game_version } else { 'none' })), installed mod: $installed -> rebuilding"
    $r = Invoke-FAPython @('-m', 'tools.autoupdate')
    if ($r.Code -ne 0) { Log ('content update FAILED: ' + ($r.Output -join ' ')); exit 1 }
    Log ('content: ' + ($r.Output | Select-Object -Last 1))
    & (Join-Path $PSScriptRoot 'install.ps1') -Version $version | ForEach-Object { Log "install: $_" }
}

# Steam updates and "verify integrity" restore the game's own files: repair them
if (-not (Test-ScenariosPatched)) { $s = Repair-Scenarios; Log "scenario texts re-patched: $($s.Patched) files" }
if ((Get-GameLanguage) -eq 'ar' -and -not (Test-LanguageNamePatched)) { Set-LanguageName; Log 'language name re-patched' }
if (-not (Test-ModEnabled)) { & (Join-Path $PSScriptRoot 'install.ps1') -Version $version | ForEach-Object { Log "install: $_" } }

# Other mods the player installed: rebuild their Arabic pack when the set of mods (or a version) changed.
# Uses the stored API key if there is one; never asks (offline otherwise). See tools\translate_mods.ps1.
$mp = Invoke-FAPython @('-m', 'tools.modpack', 'status')
if ($mp.Code -ne 0) { Log ('mods pack status failed: ' + ($mp.Output -join ' ')) }
elseif (($mp.Output[-1] | ConvertFrom-Json).changed) {
    Log 'installed mods changed: rebuilding their Arabic pack'
    try { & (Join-Path $PSScriptRoot 'translate_mods.ps1') -NonInteractive | ForEach-Object { Log "mods: $_" } }
    catch { Log "mods pack FAILED: $($_.Exception.Message)" }
}

if ($changed) {
    $v = Invoke-FAPython @('-m', 'tools.verify_game', $version)
    Log ('engine check: ' + ($v.Output | Select-Object -Last 1))
}

[pscustomobject]@{ game_version = $version; mod_version = Get-InstalledModVersion; checked_at = (Get-Date).ToString('s') } |
    ConvertTo-Json | Set-Content $stateFile -Encoding UTF8
Log "ok: game $version, mod $(Get-InstalledModVersion), language $(Get-GameLanguage)"
