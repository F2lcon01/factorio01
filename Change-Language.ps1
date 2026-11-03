# أداة لغة Factorio (مؤقتة حتى تصدر الترجمة العربية الرسمية):
#   - تغيير اللغة بين العربية والإنجليزية
#   - فحص إصدار اللعبة وإصدار المود: «متطابقة» أو زر «إصلاح»
# التشغيل: انقر مرتين على Change-Language.cmd   (يطلب صلاحيات المدير)
# بلا واجهة: -Language ar|en   -Check   -Fix        للاختبار: -NoElevate   -Snapshot <png>   -PreviewProblems
param(
    [string]$UserAppData = $env:APPDATA,
    [ValidateSet('', 'ar', 'en')][string]$Language = '',
    [switch]$Check,
    [switch]$Fix,
    [switch]$NoElevate,
    [string]$Snapshot = '',
    [switch]$PreviewProblems
)
$ErrorActionPreference = 'Stop'

# 1) صلاحيات المدير: نعيد تشغيل الملف مرفوعاً ونمرر مجلد بيانات المستخدم الحقيقي
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $NoElevate -and -not $Snapshot -and -not $Check) {
    $argList = '-NoProfile -ExecutionPolicy Bypass -STA -File "' + $PSCommandPath + '" -UserAppData "' + $UserAppData + '"'
    if ($Language) { $argList += " -Language $Language" }
    if ($Fix) { $argList += ' -Fix' }
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -Verb RunAs -ArgumentList $argList
    return
}

# الوحدة بجانب الملف (داخل المود: arabic-tools) أو في tools (داخل المشروع)
$module = Join-Path $PSScriptRoot 'FactorioArabic.psm1'
if (-not (Test-Path $module)) { $module = Join-Path $PSScriptRoot 'tools\FactorioArabic.psm1' }
Import-Module $module -Force
Set-FAUserAppData $UserAppData

$problemText = @{
    'version-mismatch' = 'إصدار المود لا يطابق إصدار اللعبة'
    'incompatible'     = 'المود غير متوافق مع إصدار اللعبة'
    'mod-missing'      = 'مود الترجمة غير مثبت'
    'mod-disabled'     = 'مود الترجمة معطّل'
    'language-name'    = 'اسم اللغة في القائمة يحتاج إصلاحاً'
    'scenarios'        = 'نصوص الدروس والسيناريوهات تحتاج إصلاحاً'
}

function Get-LanguageLabel {
    switch (Get-GameLanguage) { 'ar' { 'العربية' } 'en' { 'English' } default { 'تلقائي (حسب Steam)' } }
}

function Format-FixResult([string[]]$Codes) {
    $lines = foreach ($c in $Codes) {
        switch -Wildcard ($c) {
            'rebuilt'            { '✓ أُعيد بناء المود على إصدار اللعبة وتثبيته' }
            'fixed-name'         { '✓ أُصلح اسم اللغة في القائمة' }
            'fixed-scenarios'    { '✓ أُعيد ترقيع نصوص الدروس والسيناريوهات' }
            'enabled-mod'        { '✓ فُعِّل مود الترجمة' }
            'update-available:*' { '⬆ يوجد إصدار أحدث للمود (' + $c.Split(':')[1] + '): افتح اللعبة ← Mods ← Updates ← اضغط تحديث' }
            'install-available:*' { '⬇ مود الترجمة غير مثبت: افتح اللعبة ← Mods ← Install وابحث عن arabic-complete ثم ثبّته (' + $c.Split(':')[1] + ')' }
            'compatible-latest'  { '✓ المود متوافق مع لعبتك ويعمل. لا يوجد إصدار أحدث منه بعد، واختلاف الرقم الأخير لا يوقفه.' }
            'wait-for-update'    { '⏳ المود غير متوافق مع هذا الإصدار من اللعبة. انتظر تحديث المود.' }
            'portal-unreachable' { '⚠ تعذّر الاتصال بموقع المودات للتحقق من وجود تحديث.' }
        }
    }
    if (-not $lines) { return 'لا شيء يحتاج إصلاحاً.' }
    $lines -join "`n"
}

function Switch-GameLanguage([string]$Code) {
    if (Test-GameRunning) { return 'أغلق اللعبة أولاً ثم أعد المحاولة (اللعبة تحفظ إعداداتها عند الإغلاق).' }
    $backup = New-SettingsBackup
    Set-GameLanguage $Code
    if ($Code -eq 'en') { return "تم: لغة اللعبة الآن الإنجليزية.`nنسخة احتياطية: $backup" }
    $fixed = @(Invoke-FAFix)   # العربية تحتاج المود مفعّلاً واسم اللغة والدروس سليمة
    "تم: لغة اللعبة الآن العربية.`n" + (Format-FixResult $fixed) + "`nنسخة احتياطية: $backup"
}

# 2) بلا واجهة
if ($Check) {
    $h = Get-FAHealth
    "إصدار اللعبة: $($h.GameVersion) | إصدار المود: $($h.ModVersion) | الوضع: $($h.Mode) | اللغة: $(Get-LanguageLabel)"
    if ($h.Problems) { 'غير متطابقة: ' + (($h.Problems | ForEach-Object { $problemText[$_] }) -join '، ') } else { 'متطابقة ✓' }
    return
}
if ($Fix) {
    if (Test-GameRunning) { 'أغلق اللعبة أولاً ثم أعد المحاولة.'; return }
    Format-FixResult @(Invoke-FAFix)
    return
}
if ($Language) { Switch-GameLanguage $Language; return }

# 3) الواجهة الرسومية
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$ok = [Drawing.Color]::FromArgb(102, 187, 106)
$warn = [Drawing.Color]::FromArgb(255, 167, 38)
$form = New-Object Windows.Forms.Form
$form.Text = 'لغة Factorio'
$form.RightToLeft = 'Yes'
$form.RightToLeftLayout = $true
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ClientSize = New-Object Drawing.Size(460, 360)
$form.Font = New-Object Drawing.Font('Segoe UI', 11)
$form.BackColor = [Drawing.Color]::FromArgb(36, 36, 36)
$form.ForeColor = [Drawing.Color]::FromArgb(255, 230, 192)

function New-Label([string]$Text, [int]$Y, [int]$H, [float]$Size = 11, [bool]$Bold = $false) {
    $l = New-Object Windows.Forms.Label
    $l.Text = $Text
    $style = if ($Bold) { [Drawing.FontStyle]::Bold } else { [Drawing.FontStyle]::Regular }
    $l.Font = New-Object Drawing.Font('Segoe UI', $Size, $style)
    $l.AutoSize = $false
    $l.TextAlign = 'MiddleCenter'
    $l.SetBounds(20, $Y, 420, $H)
    $l
}
function New-Button([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, [Drawing.Color]$Color) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $Text
    $b.Font = New-Object Drawing.Font('Segoe UI', 13, [Drawing.FontStyle]::Bold)
    $b.SetBounds($X, $Y, $W, $H)
    $b.FlatStyle = 'Flat'
    $b.BackColor = $Color
    $b.ForeColor = [Drawing.Color]::White
    $b.Cursor = 'Hand'
    $b
}

$title = New-Label 'أداة لغة Factorio' 12 34 15 $true
$title.ForeColor = [Drawing.Color]::FromArgb(255, 156, 0)

$versions = New-Label '' 52 26 11
$state = New-Label '' 80 26 11 $true
$details = New-Label '' 106 44 9.5
$details.ForeColor = [Drawing.Color]::FromArgb(200, 200, 200)
$btnFix = New-Button 'إصلاح' 150 152 160 40 $warn

$sep = New-Object Windows.Forms.Label
$sep.SetBounds(30, 204, 400, 1)
$sep.BackColor = [Drawing.Color]::FromArgb(80, 80, 80)

$current = New-Label '' 212 26 11
$btnAr = New-Button 'العربية' 250 244 180 56 ([Drawing.Color]::FromArgb(46, 125, 50))
$btnEn = New-Button 'English' 30 244 180 56 ([Drawing.Color]::FromArgb(69, 90, 100))
$footer = New-Label 'أغلق اللعبة قبل أي تغيير. يعمل بصلاحيات المدير.' 312 36 9
$footer.ForeColor = [Drawing.Color]::FromArgb(160, 160, 160)

function Update-Status {
    $h = Get-FAHealth
    $problems = @($h.Problems)
    if ($PreviewProblems) { $problems = @('version-mismatch', 'scenarios') }
    $mv = if ($h.ModVersion) { $h.ModVersion } else { 'غير مثبت' }
    $versions.Text = "إصدار اللعبة: $($h.GameVersion)     إصدار المود: $mv"
    if ($problems.Count -eq 0) {
        $state.Text = '✓ متطابقة — كل شيء سليم'
        $state.ForeColor = $ok
        $details.Text = ''
        $btnFix.Visible = $false
    } else {
        $state.Text = '⚠ غير متطابقة — يحتاج إصلاحاً'
        $state.ForeColor = $warn
        $details.Text = ($problems | ForEach-Object { $problemText[$_] }) -join ' • '
        $btnFix.Visible = $true
    }
    $current.Text = 'اللغة الحالية: ' + (Get-LanguageLabel)
}

function Show-Message([string]$Text) {
    [void][Windows.Forms.MessageBox]::Show($form, $Text, 'لغة Factorio', 'OK', 'Information', 'Button1',
        [Windows.Forms.MessageBoxOptions]::RtlReading -bor [Windows.Forms.MessageBoxOptions]::RightAlign)
}

$run = {
    param($action)
    $form.Cursor = 'WaitCursor'
    try { $msg = & $action } catch { $msg = 'حدث خطأ: ' + $_.Exception.Message }
    $form.Cursor = 'Default'
    Update-Status
    Show-Message $msg
}
$btnAr.Add_Click({ & $run { Switch-GameLanguage 'ar' } })
$btnEn.Add_Click({ & $run { Switch-GameLanguage 'en' } })
$btnFix.Add_Click({
    & $run {
        if (Test-GameRunning) { return 'أغلق اللعبة أولاً ثم أعد المحاولة.' }
        $codes = @(Invoke-FAFix)
        $text = Format-FixResult $codes
        if ($codes -like '*-available:*') { Start-Process 'https://mods.factorio.com/mod/arabic-complete' }
        $text
    }
})

$form.Controls.AddRange(@($title, $versions, $state, $details, $btnFix, $sep, $current, $btnAr, $btnEn, $footer))
Update-Status

if ($Snapshot) {   # للتحقق: رسم النافذة في صورة دون إظهارها
    $form.Opacity = 0
    $form.Show()
    $form.Refresh()
    $bmp = New-Object Drawing.Bitmap($form.Width, $form.Height)
    $form.DrawToBitmap($bmp, (New-Object Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
    $bmp.Save($Snapshot, [Drawing.Imaging.ImageFormat]::Png)
    $form.Close()
    return
}
[void]$form.ShowDialog()
