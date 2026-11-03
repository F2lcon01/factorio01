#Requires -Version 7
# Publish / update arabic-complete on mods.factorio.com with YOUR API key. The key is read from your own terminal's
# environment, never written to disk, never printed.
# Create the key at https://factorio.com/profile with usages: "ModPortal: Publish Mods", "Upload Mods", "Edit Mods".
#   (the script asks for the key with hidden input; or set $env:FACTORIO_API_KEY yourself beforehand)
#   pwsh -File tools\publish.ps1 -Version 1.0.0 -DryRun     # validate locally, no network
#   pwsh -File tools\publish.ps1 -Version 1.0.0             # first publish (creates the mod)
#   pwsh -File tools\publish.ps1 -Version 1.0.1 -Update     # later releases
# API: https://wiki.factorio.com/Mod_publish_API, Mod_upload_API, Mod_details_API
param([Parameter(Mandatory)][string]$Version, [switch]$Update, [switch]$DryRun)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = Split-Path $PSScriptRoot -Parent
$name = 'arabic-complete'
$zip = Join-Path $root "dist\${name}_$Version.zip"
if (-not (Test-Path $zip)) { throw "missing $zip — run: python -E -m tools.package $Version" }
$meta = Get-Content (Join-Path $root 'mod\portal.json') -Raw -Encoding utf8 | ConvertFrom-Json
$desc = Get-Content (Join-Path $root 'mod\portal-description.md') -Raw -Encoding utf8

$z = [IO.Compression.ZipFile]::OpenRead($zip)
try {
    $entry = $z.GetEntry("${name}_$Version/info.json")
    if (-not $entry) { throw "zip lacks ${name}_$Version/info.json" }
    $info = (New-Object IO.StreamReader($entry.Open())).ReadToEnd() | ConvertFrom-Json
    $cfgs = @($z.Entries | Where-Object FullName -like "${name}_$Version/locale/ar/*.cfg").Count
    $exe = @($z.Entries | Where-Object { $_.FullName -match '\.(exe|bat|cmd|ps1|psm1|sh|py)$' } | ForEach-Object FullName)
} finally { $z.Dispose() }
if ($info.name -ne $name -or $info.version -ne $Version) { throw "info.json says $($info.name) $($info.version)" }
if ($cfgs -ne 6) { throw "expected 6 locale files, found $cfgs" }
if ($exe) { throw "the portal rejects executable files in a mod: $($exe -join ', ')" }   # InvalidModUpload

$mode = if ($Update) { 'new release' } else { 'first publish' }
Write-Output "$mode : $name $Version  ($([math]::Round((Get-Item $zip).Length / 1KB)) KB, $cfgs locale files, factorio $($info.factorio_version))"
Write-Output "title   : $($meta.title)"
Write-Output "category: $($meta.category)   license: $($meta.license)"
if ($DryRun) { Write-Output 'dry run: nothing sent'; return }

$key = $env:FACTORIO_API_KEY
if (-not $key) {  # hidden prompt: the key is typed by you, never echoed, never stored
    $key = [Net.NetworkCredential]::new('', (Read-Host 'Factorio API key' -AsSecureString)).Password
}
if (-not $key) { throw 'no API key given' }
$h = @{ Authorization = "Bearer $key" }
$base = 'https://mods.factorio.com/api/v2/mods'
if ($Update) {
    $init = Invoke-RestMethod -Method Post -Uri "$base/releases/init_upload" -Headers $h -Form @{ mod = $name }
    $res = Invoke-RestMethod -Method Post -Uri $init.upload_url -Form @{ file = Get-Item $zip }
} else {
    $init = Invoke-RestMethod -Method Post -Uri "$base/init_publish" -Headers $h -Form @{ mod = $name }
    $res = Invoke-RestMethod -Method Post -Uri $init.upload_url -Form @{
        file = Get-Item $zip; description = $desc; category = $meta.category; license = $meta.license }
}
if (-not $res.success) { throw "$($res.error): $($res.message)" }
Write-Output "published: https://mods.factorio.com/mod/$name"
$env:FACTORIO_API_KEY = $key   # this process only: the page (text, FAQ, gallery) follows every release
try { & (Join-Path $PSScriptRoot 'portal_page.ps1') } finally { Remove-Item Env:FACTORIO_API_KEY -ErrorAction SilentlyContinue }
