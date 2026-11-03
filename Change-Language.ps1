# تغيير لغة Factorio بين العربية والإنجليزية — بواجهة رسومية وبصلاحيات المدير.
# التشغيل: انقر مرتين على Change-Language.cmd  (أو: powershell -STA -File Change-Language.ps1)
# بلا واجهة: -Language ar | en      اختبار بلا مدير: -NoElevate      صورة للنافذة: -Snapshot <png>
param(
    [string]$UserAppData = $env:APPDATA,
    [ValidateSet('', 'ar', 'en')][string]$Language = '',
    [switch]$NoElevate,
    [string]$Snapshot = ''
)
$ErrorActionPreference = 'Stop'

# 1) صلاحيات المدير: نعيد تشغيل الملف نفسه مرفوعاً، ونمرر مجلد بيانات المستخدم الحقيقي
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $NoElevate -and -not $Snapshot) {
    $argList = '-NoProfile -ExecutionPolicy Bypass -STA -File "' + $PSCommandPath + '" -UserAppData "' + $UserAppData + '"'
    if ($Language) { $argList += " -Language $Language" }
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -Verb RunAs -ArgumentList $argList
    return
}

Import-Module (Join-Path $PSScriptRoot 'tools\FactorioArabic.psm1') -Force
Set-FAUserAppData $UserAppData

function Get-LanguageLabel {
    switch (Get-GameLanguage) { 'ar' { 'العربية' } 'en' { 'English' } default { 'تلقائي (حسب Steam)' } }
}

function Switch-GameLanguage([string]$Code) {
    if (Test-GameRunning) { return 'أغلق اللعبة أولاً ثم أعد المحاولة (اللعبة تحفظ إعداداتها عند الإغلاق).' }
    $backup = New-SettingsBackup
    if ($Code -eq 'en') {
        Set-GameLanguage 'en'
        return "تم: لغة اللعبة الآن الإنجليزية.`nنسخة احتياطية: $backup"
    }
    Set-GameLanguage 'ar'
    $notes = @()
    if (-not (Test-LanguageNamePatched)) { Set-LanguageName; $notes += 'إصلاح اسم اللغة في القائمة' }
    if (-not (Get-InstalledModVersion) -or -not (Test-ModEnabled)) {
        & (Join-Path (Get-FARoot) 'tools\auto_update.ps1') -Force | Out-Null
        $notes += 'تثبيت مود الترجمة وتفعيله'
    }
    if (-not (Test-ScenariosPatched)) { [void](Repair-Scenarios); $notes += 'ترقيع نصوص الدروس والسيناريوهات' }
    $extra = if ($notes) { "`nوأيضاً: " + ($notes -join '، ') } else { '' }
    "تم: لغة اللعبة الآن العربية.$extra`nنسخة احتياطية: $backup"
}

# 2) بلا واجهة (للسكربتات والاختبار)
if ($Language) { Switch-GameLanguage $Language; return }

# 3) الواجهة الرسومية
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$font = New-Object Drawing.Font('Segoe UI', 11)
$form = New-Object Windows.Forms.Form
$form.Text = 'لغة Factorio'
$form.RightToLeft = 'Yes'
$form.RightToLeftLayout = $true
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ClientSize = New-Object Drawing.Size(440, 250)
$form.Font = $font
$form.BackColor = [Drawing.Color]::FromArgb(36, 36, 36)
$form.ForeColor = [Drawing.Color]::FromArgb(255, 230, 192)

$title = New-Object Windows.Forms.Label
$title.Text = 'اختر لغة اللعبة'
$title.Font = New-Object Drawing.Font('Segoe UI', 15, [Drawing.FontStyle]::Bold)
$title.ForeColor = [Drawing.Color]::FromArgb(255, 156, 0)
$title.AutoSize = $false
$title.TextAlign = 'MiddleCenter'
$title.SetBounds(20, 16, 400, 36)

$current = New-Object Windows.Forms.Label
$current.Text = 'اللغة الحالية: ' + (Get-LanguageLabel)
$current.AutoSize = $false
$current.TextAlign = 'MiddleCenter'
$current.SetBounds(20, 56, 400, 28)

function New-Choice([string]$Text, [int]$X, [Drawing.Color]$Color) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $Text
    $b.Font = New-Object Drawing.Font('Segoe UI', 14, [Drawing.FontStyle]::Bold)
    $b.SetBounds($X, 100, 180, 64)
    $b.FlatStyle = 'Flat'
    $b.BackColor = $Color
    $b.ForeColor = [Drawing.Color]::White
    $b.Cursor = 'Hand'
    $b
}
$btnAr = New-Choice 'العربية' 230 ([Drawing.Color]::FromArgb(46, 125, 50))
$btnEn = New-Choice 'English' 30 ([Drawing.Color]::FromArgb(69, 90, 100))

$status = New-Object Windows.Forms.Label
$status.Text = 'يعمل بصلاحيات المدير. أغلق اللعبة قبل التغيير.'
$status.AutoSize = $false
$status.TextAlign = 'MiddleCenter'
$status.ForeColor = [Drawing.Color]::FromArgb(180, 180, 180)
$status.SetBounds(20, 180, 400, 52)

$onChoice = {
    param($code)
    $form.Cursor = 'WaitCursor'
    try { $msg = Switch-GameLanguage $code } catch { $msg = 'حدث خطأ: ' + $_.Exception.Message }
    $form.Cursor = 'Default'
    $current.Text = 'اللغة الحالية: ' + (Get-LanguageLabel)
    [void][Windows.Forms.MessageBox]::Show($form, $msg, 'لغة Factorio', 'OK', 'Information',
        'Button1', [Windows.Forms.MessageBoxOptions]::RtlReading -bor [Windows.Forms.MessageBoxOptions]::RightAlign)
}
$btnAr.Add_Click({ & $onChoice 'ar' })
$btnEn.Add_Click({ & $onChoice 'en' })
$form.Controls.AddRange(@($title, $current, $btnAr, $btnEn, $status))

if ($Snapshot) {   # verification: render the window to an image without showing it
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
