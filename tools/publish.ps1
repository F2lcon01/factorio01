#Requires -Version 7
# Publish / update arabic-complete on mods.factorio.com with YOUR API key. The key is read from your own terminal's
# environment, never written to disk, never printed.
# Create the key at https://factorio.com/profile with usages: "ModPortal: Publish Mods", "Upload Mods", "Edit Mods".
#   $env:FACTORIO_API_KEY = '<your key>'
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
} finally { $z.Dispose() }
if ($info.name -ne $name -or $info.version -ne $Version) { throw "info.json says $($info.name) $($info.version)" }
if ($cfgs -ne 6) { throw "expected 6 locale files, found $cfgs" }

$mode = if ($Update) { 'new release' } else { 'first publish' }
Write-Output "$mode : $name $Version  ($([math]::Round((Get-Item $zip).Length / 1KB)) KB, $cfgs locale files, factorio $($info.factorio_version))"
Write-Output "title   : $($meta.title)"
Write-Output "category: $($meta.category)   license: $($meta.license)"
if ($DryRun) { Write-Output 'dry run: nothing sent'; return }

if (-not $env:FACTORIO_API_KEY) { throw 'set $env:FACTORIO_API_KEY in this terminal first' }
$h = @{ Authorization = "Bearer $($env:FACTORIO_API_KEY)" }
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
$d = Invoke-RestMethod -Method Post -Uri "$base/edit_details" -Headers $h -Form @{ mod = $name; title = $meta.title; summary = $meta.summary }
if (-not $d.success) { throw "details: $($d.error): $($d.message)" }
Write-Output "published: https://mods.factorio.com/mod/$name"
