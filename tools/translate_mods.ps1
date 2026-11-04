# Arabic for the other mods you install (generated pack 'arabic-mods-local', see tools\modpack.py).
# Needs an API key from any provider the first time: asks for it once, checks it, then stores it encrypted.
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\translate_mods.ps1               # translate + install
#   ... -Offline         no API calls: overrides, cache, the mods' own Arabic and our existing translations only
#   ... -ResetKey        forget the stored key, then ask for a new one
#   ... -Uninstall       rollback: disable the pack and park it in mods-parked (nothing is deleted)
#   ... -NonInteractive  never ask (used by tools\auto_update.ps1): without a stored key it runs offline
#   ... -Provider openai|anthropic|gemini|openrouter|groq|xai|deepseek|mistral|together|deepl|deepl-free
#   ... -BaseUrl http://localhost:11434/v1   any OpenAI-compatible server (Ollama, LM Studio...)    -Model <id>
# The key is stored for this Windows user only, encrypted with DPAPI, in
# %APPDATA%\Factorio\arabic-tools\translator-key.txt (never in the project, never printed). Python receives it
# through FA_TRANSLATE_KEY in its own process only. Windows PowerShell 5.1 and 7. ASCII only (see FactorioArabic.psm1).
param([switch]$Offline, [switch]$ResetKey, [switch]$Uninstall, [switch]$NonInteractive,
      [string]$Provider = '', [string]$BaseUrl = '', [string]$Model = '')
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'FactorioArabic.psm1') -Force
$install = Join-Path $PSScriptRoot 'install.ps1'
$keyFile = Join-Path $env:APPDATA 'Factorio\arabic-tools\translator-key.txt'
$pack = 'arabic-mods-local'
$packVersion = '1.0.0'

if (Test-GameRunning) { throw 'Factorio is running; close it first.' }
if ($Uninstall) { & $install -Name $pack -Uninstall; return }
if ($ResetKey -and (Test-Path $keyFile)) { [IO.File]::Delete($keyFile); Write-Output 'stored key forgotten' }

function ConvertTo-Plain($secure) { [Net.NetworkCredential]::new('', $secure).Password }

$key = ''
$newKey = $null
if (-not $Offline) {
    if (Test-Path $keyFile) {
        try { $key = ConvertTo-Plain (Get-Content $keyFile -Raw | ConvertTo-SecureString) }
        catch { Write-Output 'stored key unreadable (another Windows user or machine?); asking again' }
    }
    if (-not $key -and -not $NonInteractive) {
        Write-Output 'Paste an API key from any provider: OpenAI, Google Gemini, Anthropic Claude, DeepL, OpenRouter,'
        Write-Output 'Groq, DeepSeek, Mistral, xAI... (input is hidden; press Enter with nothing to run offline)'
        $newKey = Read-Host 'API key' -AsSecureString
        $key = (ConvertTo-Plain $newKey).Trim()
    }
}

$names = 'FA_TRANSLATE_KEY', 'FA_TRANSLATE_PROVIDER', 'FA_TRANSLATE_BASE_URL', 'FA_TRANSLATE_MODEL'
$env:FA_TRANSLATE_KEY = $key
$env:FA_TRANSLATE_PROVIDER = $Provider
$env:FA_TRANSLATE_BASE_URL = $BaseUrl
$env:FA_TRANSLATE_MODEL = $Model
try {
    if ($key) {
        $probe = Invoke-FAPython @('-m', 'tools.translator', 'probe')
        if ($probe.Code -ne 0) { throw ('the key was not accepted: ' + ($probe.Output -join ' ')) }
        $cfg = $probe.Output[-1] | ConvertFrom-Json
        Write-Output "translator: $($cfg.provider) / $($cfg.model)"
        if ($newKey) {   # stored only after a provider accepted it
            New-Item -ItemType Directory -Force (Split-Path $keyFile -Parent) | Out-Null
            [IO.File]::WriteAllText($keyFile, ($newKey | ConvertFrom-SecureString))
            Write-Output "key stored for this Windows user (encrypted): $keyFile"
        }
    } else {
        Write-Output 'no API key: offline build (strings without a translation stay in English)'
    }
    $pyArgs = @('-m', 'tools.modpack', 'build')
    if (-not $key) { $pyArgs += '--offline' }
    $r = Invoke-FAPython $pyArgs
    $r.Output | ForEach-Object { Write-Output $_ }
    if ($r.Code -ne 0) { throw 'pack build failed' }
} finally {
    foreach ($n in $names) { [Environment]::SetEnvironmentVariable($n, $null, 'Process') }
    $key = $null
}
& $install -Name $pack -Version $packVersion
Write-Output 'details: reports\modpack.md'
