#Requires -Version 7
# Mod portal page of arabic-complete: gallery images + title, summary, description, FAQ, links. No new release.
# Images: docs/portal/*.png (made by python -E -m tools.portal_images <v>), shown in file-name order.
# In mod/portal-description.md and mod/portal-faq.md, {{img:<file name without .png>}} becomes the image's portal URL.
# Uploaded images are remembered in mod/portal-images.json (by SHA1) so an unchanged image is not uploaded again.
#   pwsh -File tools\portal_page.ps1 -DryRun     # local checks only, no network
#   pwsh -File tools\portal_page.ps1             # asks for the API key with hidden input (or $env:FACTORIO_API_KEY)
# The key needs the usage "ModPortal: Edit Mods". Called by publish.ps1 after every release.
# API: https://wiki.factorio.com/Mod_images_API, https://wiki.factorio.com/Mod_details_API
param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$name = 'arabic-complete'
$meta = Get-Content (Join-Path $root 'mod\portal.json') -Raw -Encoding utf8 | ConvertFrom-Json
$desc = Get-Content (Join-Path $root 'mod\portal-description.md') -Raw -Encoding utf8
$faq = Get-Content (Join-Path $root 'mod\portal-faq.md') -Raw -Encoding utf8
$cachePath = Join-Path $root 'mod\portal-images.json'
$cache = if (Test-Path $cachePath) { Get-Content $cachePath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable } else { @{} }
$images = @(Get-ChildItem (Join-Path $root 'docs\portal') -Filter '*.png' | Sort-Object Name)

$wanted = [regex]::Matches($desc + $faq, '\{\{img:([^}]+)\}\}') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
$missing = @($wanted | Where-Object { $_ -notin $images.BaseName })
if ($missing) { throw "placeholders without an image in docs\portal: $($missing -join ', ')" }
foreach ($i in $images) { if ($i.Length -gt 4MB) { throw "$($i.Name) is over 4 MB" } }
Write-Output "images : $($images.Count) ($(($images.Name) -join ', '))"
Write-Output "text   : description $($desc.Length) chars, faq $($faq.Length) chars, placeholders $(@($wanted).Count)"
if ($DryRun) { Write-Output 'dry run: nothing sent'; return }

$key = $env:FACTORIO_API_KEY
if (-not $key) { $key = [Net.NetworkCredential]::new('', (Read-Host 'Factorio API key' -AsSecureString)).Password }
if (-not $key) { throw 'no API key given' }
$h = @{ Authorization = "Bearer $key" }
$base = 'https://mods.factorio.com/api/v2/mods'
function Assert-Ok($r, $what) { if ($r.PSObject.Properties['success'] -and -not $r.success) { throw "${what}: $($r.error): $($r.message)" } }

$ids = @()
foreach ($i in $images) {
    $sha = (Get-FileHash $i.FullName -Algorithm SHA1).Hash.ToLower()
    $c = $cache[$i.BaseName]
    if (-not $c -or $c.sha1 -ne $sha) {
        $init = Invoke-RestMethod -Method Post -Uri "$base/images/add" -Headers $h -Form @{ mod = $name }
        Assert-Ok $init 'images/add'
        $up = Invoke-RestMethod -Method Post -Uri $init.upload_url -Form @{ image = $i }
        Assert-Ok $up "upload $($i.Name)"
        $c = @{ sha1 = $sha; id = $up.id; url = $up.url; thumbnail = $up.thumbnail }
        $cache[$i.BaseName] = $c
        Write-Output "uploaded: $($i.Name)"
    }
    $ids += $c.id
    $desc = $desc.Replace("{{img:$($i.BaseName)}}", $c.url)
    $faq = $faq.Replace("{{img:$($i.BaseName)}}", $c.url)
}
[IO.File]::WriteAllText($cachePath, ($cache | ConvertTo-Json -Depth 3) + "`n", (New-Object Text.UTF8Encoding $false))
$g = Invoke-RestMethod -Method Post -Uri "$base/images/edit" -Headers $h -Form @{ mod = $name; images = ($ids -join ',') }
Assert-Ok $g 'images/edit'
$d = Invoke-RestMethod -Method Post -Uri "$base/edit_details" -Headers $h -Form @{
    mod = $name; title = $meta.title; summary = $meta.summary; description = $desc; faq = $faq
    homepage = $meta.homepage; source_url = $meta.source_url }
Assert-Ok $d 'edit_details'
Write-Output "page updated: https://mods.factorio.com/mod/$name ($($ids.Count) gallery images)"
