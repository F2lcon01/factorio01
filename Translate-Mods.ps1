# أداة ترجمة المودات الإضافية (نافذة):
#   - تعرض المودات المفعّلة وحالة كل مود: مترجم، جديد، تغيّر، ينتظر الترجمة، بلغته الأصلية
#   - خانة اختيار لكل مود: بلا علامة = يبقى بلغته الأصلية (ترجماته تبقى في الذاكرة لإعادته بلا طلبات)
#   - مفتاح API من أي مزوّد، يُحفظ مشفّراً لمستخدم Windows الحالي فقط
#   - ترجمة وتثبيت مع شريط تقدّم، وملخص الاستهلاك والتوفير
# التشغيل: انقر مرتين على Translate-Mods.cmd   (لا يحتاج صلاحيات المدير)
# المحرك: tools\modpack.py (Python المشروع، أو Python المدمج في حزمة اللاعبين)
# للاختبار والتوثيق: -Snapshot <png>   -PreviewBusy
param(
    [string]$UserAppData = $env:APPDATA,
    [string]$Snapshot = '',
    [switch]$PreviewBusy
)
$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot 'FactorioArabic.psm1'
if (-not (Test-Path $module)) { $module = Join-Path $PSScriptRoot 'tools\FactorioArabic.psm1' }
Import-Module $module -Force
Set-FAUserAppData $UserAppData

$pack = 'arabic-mods-local'
$stateDir = Get-FAStateDir
$reportPath = if (Test-EmbeddedPython) { Join-Path $PSScriptRoot 'app\reports\modpack.md' } else { Join-Path (Get-FARoot) 'reports\modpack.md' }
$work = Join-Path $env:TEMP 'fa-translator'
New-Item -ItemType Directory -Force $work | Out-Null

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$bg = [Drawing.Color]::FromArgb(36, 36, 36)
$panel = [Drawing.Color]::FromArgb(49, 48, 49)
$text = [Drawing.Color]::FromArgb(255, 230, 192)
$orange = [Drawing.Color]::FromArgb(255, 156, 0)
$muted = [Drawing.Color]::FromArgb(170, 170, 170)
$stateColor = @{
    translated = [Drawing.Color]::FromArgb(129, 199, 132)
    new        = [Drawing.Color]::FromArgb(100, 181, 246)
    changed    = [Drawing.Color]::FromArgb(255, 167, 38)
    pending    = [Drawing.Color]::FromArgb(255, 213, 79)
    original   = [Drawing.Color]::FromArgb(170, 170, 170)
}

$form = New-Object Windows.Forms.Form
$form.Text = 'ترجمة المودات الإضافية — الإصدار ' + (N (Get-FAToolsVersion))
$form.RightToLeft = 'Yes'
$form.RightToLeftLayout = $true
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.ClientSize = New-Object Drawing.Size(820, 678)
$form.Font = New-Object Drawing.Font('Segoe UI', 10)
$form.BackColor = $bg
$form.ForeColor = $text

function New-Label([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, [float]$Size = 10, [bool]$Bold = $false) {
    $l = New-Object Windows.Forms.Label
    $l.Text = $Text
    $l.Font = New-Object Drawing.Font('Segoe UI', $Size, $(if ($Bold) { [Drawing.FontStyle]::Bold } else { [Drawing.FontStyle]::Regular }))
    $l.SetBounds($X, $Y, $W, $H)
    $l
}
function New-Button([string]$Text, [int]$X, [int]$Y, [int]$W, [int]$H, [Drawing.Color]$Color) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $Text
    $b.Font = New-Object Drawing.Font('Segoe UI', 10, [Drawing.FontStyle]::Bold)
    $b.SetBounds($X, $Y, $W, $H)
    $b.FlatStyle = 'Flat'
    $b.BackColor = $Color
    $b.ForeColor = [Drawing.Color]::White
    $b.Cursor = 'Hand'
    $b
}

$title = New-Label 'ترجمة المودات الإضافية إلى العربية' 20 12 470 32 15 $true
$title.ForeColor = $orange
# this tool's version, and whether it or the Arabic mod has a newer release (checked in the background)
$versionLink = New-Object Windows.Forms.LinkLabel
$versionLink.Font = New-Object Drawing.Font('Segoe UI', 9.5)
$versionLink.AutoSize = $false
$versionLink.TextAlign = 'MiddleRight'
$versionLink.SetBounds(500, 16, 300, 26)
$versionLink.ForeColor = $muted
$versionLink.LinkColor = $orange
$versionLink.ActiveLinkColor = $orange
$versionLink.Text = 'الإصدار ' + (N (Get-FAToolsVersion)) + ' · التحقق من التحديثات...'
$versionLink.LinkArea = New-Object Windows.Forms.LinkArea(0, 0)
$script:updateUrl = $null
$versionLink.Add_LinkClicked({ if ($script:updateUrl) { Start-Process $script:updateUrl } })
$subtitle = New-Label 'تُترجم نصوص كل مود تضيفه، وتُحفظ كل ترجمة في ذاكرة مشتركة فلا يُطلب النص نفسه مرتين. أزل العلامة عن مود لإبقائه بلغته الأصلية.' 20 46 780 22 9.5
$subtitle.ForeColor = $muted

$list = New-Object Windows.Forms.ListView
$list.View = 'Details'
$list.CheckBoxes = $true   # ticked = Arabic; unticked = the language the mod ships (its translations stay in the memory)
$list.FullRowSelect = $true
$list.HeaderStyle = 'Nonclickable'
$list.RightToLeftLayout = $true
$list.BackColor = $panel
$list.ForeColor = $text
$list.BorderStyle = 'None'
$list.SetBounds(20, 76, 780, 200)
foreach ($c in @(@('المود', 250), @('الإصدار', 90), @('النصوص', 80), @('بالعربية', 90), @('تنتظر', 80), @('الحالة', 170))) {
    [void]$list.Columns.Add($c[0], $c[1])
}

$keyBox = New-Object Windows.Forms.GroupBox
$keyBox.Text = 'مفتاح API: اختر المزوّد، أو «تلقائي» إن كان شكل المفتاح يدل عليه'
$keyBox.ForeColor = $text
$keyBox.SetBounds(20, 286, 780, 120)
# a key is sent to one provider only: the one its format names, or the one chosen here
$providers = @(
    @('تلقائي (من شكل المفتاح)', ''), @('Google Gemini (مجاني)', 'gemini'), @('OpenRouter: نماذج مجانية فقط', 'openrouter-free'),
    @('OpenRouter: كل النماذج (مدفوعة)', 'openrouter'), @('OpenAI', 'openai'), @('Anthropic Claude', 'anthropic'),
    @('DeepL', 'deepl'), @('Groq', 'groq'), @('DeepSeek', 'deepseek'), @('Mistral', 'mistral'),
    @('xAI (Grok)', 'xai'), @('Together', 'together'), @('Hugging Face', 'huggingface'), @('Cerebras', 'cerebras'),
    @('Fireworks', 'fireworks'), @('NVIDIA', 'nvidia'), @('خادم محلي مجاني (Ollama)', 'custom'))   # also LM Studio
$providerLabel = New-Label 'المزوّد:' 700 28 60 24 9.5
$providerBox = New-Object Windows.Forms.ComboBox
$providerBox.DropDownStyle = 'DropDownList'
$providerBox.SetBounds(470, 25, 225, 26)
foreach ($p in $providers) { [void]$providerBox.Items.Add($p[0]) }
$keyInput = New-Object Windows.Forms.TextBox
$keyInput.UseSystemPasswordChar = $true
$keyInput.RightToLeft = 'No'
$keyInput.SetBounds(240, 25, 222, 26)
$btnKey = New-Button 'حفظ وتحقق' 120 23 110 30 ([Drawing.Color]::FromArgb(69, 90, 100))
$btnForget = New-Button 'نسيان' 20 23 90 30 ([Drawing.Color]::FromArgb(90, 60, 60))
$urlLabel = New-Label 'رابط الخادم:' 680 60 80 24 9.5
$urlInput = New-Object Windows.Forms.TextBox
$urlInput.RightToLeft = 'No'
$urlInput.Text = 'http://localhost:11434/v1'
$urlInput.SetBounds(240, 58, 435, 26)
$keyState = New-Label '' 20 90 740 24 9.5
# opens the provider's official key page; the player creates the key there and pastes it here
$btnFreeKey = New-Button 'احصل على مفتاح مجاني' 470 56 225 30 ([Drawing.Color]::FromArgb(46, 125, 50))
$keyBox.Controls.AddRange(@($providerLabel, $providerBox, $keyInput, $btnKey, $btnForget, $urlLabel, $urlInput, $btnFreeKey, $keyState))

function Get-ChosenProvider { $providers[[Math]::Max(0, $providerBox.SelectedIndex)][1] }
function Select-Provider([string]$Code) {
    for ($i = 0; $i -lt $providers.Count; $i++) { if ($providers[$i][1] -eq $Code) { $providerBox.SelectedIndex = $i } }
}
function Update-ProviderFields {
    $custom = (Get-ChosenProvider) -eq 'custom'
    $urlLabel.Visible = $custom
    $urlInput.Visible = $custom
    $btnFreeKey.Visible = -not $custom
}
$choice = Get-FAProviderChoice
$providerBox.SelectedIndex = 0
# first run, no key yet: suggest Google Gemini (free, and its key page is one click away)
if (-not (Test-FAProviderChoice) -and -not (Get-FATranslatorKey)) { Select-Provider 'gemini' } else { Select-Provider $choice.provider }
if ($choice.base_url) { $urlInput.Text = $choice.base_url }
Update-ProviderFields
$providerBox.Add_SelectedIndexChanged({ Update-ProviderFields })

$btnTranslate = New-Button 'ترجمة وتثبيت' 600 420 200 44 ([Drawing.Color]::FromArgb(46, 125, 50))
$btnTranslate.Font = New-Object Drawing.Font('Segoe UI', 12, [Drawing.FontStyle]::Bold)
$btnRefresh = New-Button 'تحديث القائمة' 450 426 140 34 ([Drawing.Color]::FromArgb(69, 90, 100))
$btnReport = New-Button 'فتح التقرير' 300 426 140 34 ([Drawing.Color]::FromArgb(69, 90, 100))
$btnUndo = New-Button 'إلغاء التثبيت (تراجع)' 20 426 270 34 ([Drawing.Color]::FromArgb(90, 60, 60))

$bar = New-Object Windows.Forms.ProgressBar
$bar.SetBounds(20, 476, 780, 18)
$bar.RightToLeftLayout = $true
$barText = New-Label 'جاهز.' 20 498 780 22 9.5
$barText.ForeColor = $muted

$summary = New-Object Windows.Forms.TextBox
$summary.Multiline = $true
$summary.ReadOnly = $true
$summary.BorderStyle = 'None'
$summary.BackColor = $panel
$summary.ForeColor = $text
$summary.Font = New-Object Drawing.Font('Segoe UI', 9.5)
$summary.SetBounds(20, 526, 780, 116)
$footer = New-Label 'أغلق اللعبة قبل الترجمة. المفتاح يُحفظ مشفّراً لمستخدم Windows الحالي فقط، ولا يُرسل إلا إلى المزوّد الذي اخترته.' 20 648 780 22 9
$footer.ForeColor = $muted

$form.Controls.AddRange(@($title, $versionLink, $subtitle, $list, $keyBox, $btnTranslate, $btnRefresh, $btnReport, $btnUndo, $bar, $barText, $summary, $footer))

# ---------- data ----------
function Read-Json([string]$Path) { if (Test-Path $Path) { Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null } }
# N (numbers as Western digits in right-to-left text) comes from FactorioArabic.psm1

# ---------- versions: this tool and the Arabic mod, against the newest online ----------
function Format-Updates($U) {
    # -> @{ Text; Url } for the version line; Url only when there is something newer to get
    $t, $m, $parts, $url = $U.Tools, $U.Mod, @(), $null
    if ($t.Newer) { $parts += "⬆ أداة أحدث: $(N $t.Latest)"; $url = $t.Url }
    if ($m.Newer) { $parts += "⬆ مود أحدث: $(N $m.Latest)"; if (-not $url) { $url = $m.Url } }
    if (-not $parts) {
        $parts += $(if ($t.Latest -and $m.Latest -and $m.Current) { '✓ الأداة والمود بآخر إصدار' }
                    elseif ($t.Latest) { '✓ الأداة بآخر إصدار' } else { 'تعذّر التحقق من التحديثات' })
    }
    $text = ($parts -join ' · ')
    if ($url) { $text += ' (اضغط هنا)' }
    @{ Text = $text; Url = $url }
}

function Show-Updates($U) {
    $f = Format-Updates $U
    $versionLink.Text = 'الإصدار ' + (N (Get-FAToolsVersion)) + ' · ' + $f.Text
    $script:updateUrl = $f.Url
    $versionLink.LinkArea = $(if ($f.Url) { New-Object Windows.Forms.LinkArea(0, $versionLink.Text.Length) } else { New-Object Windows.Forms.LinkArea(0, 0) })
    $versionLink.ForeColor = $(if ($f.Url) { $orange } elseif ($f.Text -like '✓*') { $stateColor.translated } else { $muted })
}

$script:updateCheck = $null
try { $script:updateCheck = Start-FAUpdateCheck } catch { }
$updTimer = New-Object Windows.Forms.Timer
$updTimer.Interval = 400
$updTimer.Add_Tick({
    if (-not $script:updateCheck) { $updTimer.Stop(); $versionLink.Text = 'الإصدار ' + (N (Get-FAToolsVersion)); return }
    $u = Get-FAUpdateResult $script:updateCheck
    if ($u) { $updTimer.Stop(); Show-Updates $u }
})
$updTimer.Start()

$btnFreeKey.Add_Click({
    # Google Gemini, or OpenRouter's free models when OpenRouter is chosen: both have a free tier
    if ((Get-ChosenProvider) -like 'openrouter*') { Select-Provider 'openrouter-free'; $page = 'https://openrouter.ai/keys' }
    else { Select-Provider 'gemini'; $page = 'https://aistudio.google.com/apikey' }
    Start-Process $page
    $barText.Text = 'أنشئ المفتاح في الصفحة التي فُتحت في المتصفح، ثم الصقه هنا واضغط «حفظ وتحقق».'
})

function Update-KeyState {
    $cfg = Read-Json (Join-Path $stateDir 'translator.json')
    if (Get-FATranslatorKey) {
        $who = if ($cfg) { " (المزوّد: $($cfg.config.provider) / $($cfg.config.model))" } else { '' }
        $keyState.Text = 'المفتاح: محفوظ ومشفّر' + $who
        $keyState.ForeColor = $stateColor.translated
    } else {
        $keyState.Text = 'لا يوجد مفتاح: الترجمة تعمل بما في الذاكرة فقط، والنصوص الجديدة تبقى بالإنجليزية.'
        $keyState.ForeColor = $stateColor.pending
    }
}

$script:loading = $false
function Update-Mods {
    $script:loading = $true   # filling the list must not fire the checkbox handler
    try {
        $list.Items.Clear()
        $r = Invoke-FAPython @('-m', 'tools.modpack', 'status')
        if ($r.Code -ne 0) { $barText.Text = 'تعذّرت قراءة المودات: ' + ($r.Output | Select-Object -Last 1); return }
        $st = $r.Output[-1] | ConvertFrom-Json
        foreach ($m in $st.states) {
            $label = $m.state_ar
            if ($m.state -eq 'changed') { $label += " ($(N $m.changed) نصاً)" }
            $item = New-Object Windows.Forms.ListViewItem($m.title)
            foreach ($v in @((N $m.version), (N $m.strings), (N $m.arabic), (N $m.pending), $label)) { [void]$item.SubItems.Add([string]$v) }
            $item.UseItemStyleForSubItems = $false
            $item.SubItems[5].ForeColor = $stateColor[$m.state]
            $item.Tag = $m.name
            $item.Checked = -not $m.excluded
            [void]$list.Items.Add($item)
        }
        if (-not $st.states) { [void]$list.Items.Add((New-Object Windows.Forms.ListViewItem('لا توجد مودات إضافية مفعّلة'))) }
    } finally { $script:loading = $false }
}

function Update-Summary {
    $s = Read-Json (Join-Path $stateDir 'last_run.json')
    if (-not $s) { $summary.Text = 'لم تُشغَّل الترجمة بعد.'; return }
    $nl = [Environment]::NewLine
    $summary.Text = "آخر تشغيل: $(N ($s.built_at -replace 'T', ' '))   المترجم: $(N $s.translator)" + $nl +
        "النصوص: $(N $s.strings)   بالعربية: $(N $s.arabic)   ما زال بالإنجليزية: $(N $s.english_left)   ترجمات جديدة: $(N $s.translated_now)" + $nl +
        "طلبات API: $(N $s.requests)   توكن داخل: $(N $s.input_tokens)   توكن خارج: $(N $s.output_tokens)" + $nl +
        "من الذاكرة بلا أي طلب: $(N $s.memory_hits) نصاً   التوفير المقدّر: نحو $(N $s.tokens_saved_estimate) توكن ($(N $s.tokens_per_string) توكن للنص، مقيس)" + $nl +
        "حصة المسرد من التوكن الداخل: نحو $(N $s.glossary_tokens_this_run) (يوحّد المصطلحات ولا يغني عن ترجمة الجملة)   حجم الذاكرة المشتركة: $(N $s.memory_size) نصاً"
}

$script:messages = @()
function Show-Message([string]$Text) {
    if ($Snapshot) { $script:messages += $Text; return }   # automated checks: no modal box to block them
    [void][Windows.Forms.MessageBox]::Show($form, $Text, 'ترجمة المودات', 'OK', 'Information', 'Button1',
        [Windows.Forms.MessageBoxOptions]::RtlReading -bor [Windows.Forms.MessageBoxOptions]::RightAlign)
}

function Set-Busy([bool]$Busy) {
    foreach ($b in @($btnTranslate, $btnRefresh, $btnKey, $btnForget, $btnUndo)) { $b.Enabled = -not $Busy }
    $form.Cursor = $(if ($Busy) { 'WaitCursor' } else { 'Default' })
}

# ---------- background runs (the window stays responsive) ----------
$script:job = $null
$timer = New-Object Windows.Forms.Timer
$timer.Interval = 300

function Start-Run([string[]]$PyArgs, [string]$Key, [scriptblock]$OnDone, [string]$Provider = '', [string]$BaseUrl = '') {
    $out = Join-Path $work 'out.txt'; $err = Join-Path $work 'err.txt'; $prog = Join-Path $work 'progress.jsonl'
    foreach ($f in @($out, $err, $prog)) { if (Test-Path $f) { [IO.File]::Delete($f) } }   # our own temp files
    $names = 'FA_TRANSLATE_KEY', 'FA_PROGRESS_FILE', 'FA_TRANSLATE_PROVIDER', 'FA_TRANSLATE_BASE_URL'
    $env:FA_TRANSLATE_KEY = $Key
    $env:FA_PROGRESS_FILE = $prog
    $env:FA_TRANSLATE_PROVIDER = $(if ($Provider -eq 'custom') { '' } else { $Provider })
    $env:FA_TRANSLATE_BASE_URL = $(if ($Provider -eq 'custom') { $BaseUrl } else { '' })
    try { $p = Start-FAPython $PyArgs $out $err }
    finally {   # the child has its own copy of the environment: clear ours at once
        foreach ($n in $names) { [Environment]::SetEnvironmentVariable($n, $null, 'Process') }
    }
    $script:job = @{ Process = $p; Out = $out; Err = $err; Progress = $prog; OnDone = $OnDone }
    Set-Busy $true
    $timer.Start()
}

$timer.Add_Tick({
    $j = $script:job
    if (-not $j) { $timer.Stop(); return }
    if (Test-Path $j.Progress) {
        $last = Get-Content $j.Progress -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -Last 1
        if ($last) {
            $p = $last | ConvertFrom-Json
            switch ($p.stage) {
                'scan'      { $bar.Style = 'Marquee'; $barText.Text = 'قراءة المودات والذاكرة...' }
                'translate' { $bar.Style = 'Continuous'; $bar.Maximum = [Math]::Max(1, $p.total); $bar.Value = [Math]::Min($p.done, $bar.Maximum)
                              $barText.Text = "ترجمة النصوص الجديدة: $(N $p.done) من $(N $p.total)" }
                'pack'      { $bar.Style = 'Marquee'; $barText.Text = 'بناء حزمة الترجمة...' }
                'done'      { $bar.Style = 'Continuous'; $bar.Value = $bar.Maximum; $barText.Text = 'اكتمل.' }
            }
        }
    }
    if (-not $j.Process.HasExited) { return }
    $timer.Stop()
    $script:job = $null
    $j.Process.WaitForExit()
    $stdout = @(Get-Content $j.Out -Encoding UTF8 -ErrorAction SilentlyContinue)
    $stderr = @(Get-Content $j.Err -Encoding UTF8 -ErrorAction SilentlyContinue)
    Set-Busy $false
    & $j.OnDone $j.Process.ExitCode $stdout $stderr
})

# ---------- actions ----------
function Get-KeyProblem([string[]]$Lines) {
    # translator.py's error line -> a sentence a player can act on
    $line = ($Lines | Where-Object { $_ -match 'translator:|TranslatorError|HTTP|network|timeout|UNKNOWN_FORMAT' } | Select-Object -Last 1)
    if (-not $line) { $line = ($Lines | Select-Object -Last 1) }
    if ($line -match 'UNKNOWN_FORMAT') {
        return 'شكل المفتاح لا يدل على مزوّده، فلم يُرسل إلى أي جهة. اختر المزوّد من القائمة ثم اضغط «حفظ وتحقق» مرة أخرى.'
    }
    if ($line -match 'HTTP (\d{3})[^:]*:\s*(.*)$') {
        $code, $msg = $Matches[1], $Matches[2]
        $who = 'المزوّد'
        if ($line -match 'accepted by: ([\w-]+):') { $who = $Matches[1] }
        $hint = switch -Regex ($code) {
            '^40[13]$' { 'المفتاح غير صالح لهذا المزوّد: تأكد منه، أو اختر المزوّد الصحيح من القائمة.'; break }
            '^404$'    { 'النموذج أو العنوان غير موجود: تأكد من رابط الخادم.'; break }
            '^429$'    { 'تجاوزت حدّ الطلبات المسموح (الحد المجاني غالباً). انتظر دقيقة ثم أعد المحاولة.'; break }
            '^5\d\d$'  { 'خوادم المزوّد مزدحمة الآن، والمفتاح ليس السبب. أعد المحاولة بعد دقائق.'; break }
            default    { 'جرّب مرة أخرى لاحقاً.' }
        }
        return "ردّ $who برمز الخطأ HTTP $code. $hint`n`nرسالة المزوّد: $msg"
    }
    if ($line -match 'timeout') { return 'لم يردّ المزوّد في الوقت المحدد (ضغط عنده غالباً، والمفتاح ليس السبب). أعد المحاولة بعد دقائق.' }
    if ($line -match 'network') { return 'تعذّر الاتصال بالمزوّد. تحقق من الإنترنت، أو من رابط الخادم المحلي إن اخترته.' }
    "التفاصيل:`n$line"
}

$btnKey.Add_Click({
    $provider = Get-ChosenProvider
    $baseUrl = $urlInput.Text.Trim()
    $plain = $keyInput.Text.Trim()
    if (-not $plain -and $provider -eq 'custom') { $plain = 'local' }   # a local server usually needs no key
    if (-not $plain) { Show-Message 'الصق المفتاح في الخانة أولاً.'; return }
    $secure = ConvertTo-SecureString $plain -AsPlainText -Force
    $keyInput.Text = ''
    $barText.Text = 'التحقق من المفتاح...'
    $bar.Style = 'Marquee'
    Start-Run @('-m', 'tools.translator', 'probe') $plain {
        param($code, $out, $err)
        $bar.Style = 'Continuous'
        if ($code -eq 0) {
            $cfg = $out[-1] | ConvertFrom-Json
            [void](Save-FATranslatorKey $secure)
            Save-FAProviderChoice $provider $baseUrl
            New-Item -ItemType Directory -Force $stateDir | Out-Null
            $cache = @{ tag = ''; config = $cfg } | ConvertTo-Json
            [IO.File]::WriteAllText((Join-Path $stateDir 'translator.json'), $cache, (New-Object Text.UTF8Encoding $false))
            $barText.Text = "قُبل المفتاح: $($cfg.provider) / $($cfg.model)"
        } else {
            $barText.Text = 'رُفض المفتاح، ولم يُحفظ.'
            Show-Message ('رُفض المفتاح ولم يُحفظ.' + "`n`n" + (Get-KeyProblem ($err + $out)))
        }
        Update-KeyState
    }.GetNewClosure() $provider $baseUrl
    $plain = $null
})

$btnForget.Add_Click({
    $ok = [Windows.Forms.MessageBox]::Show($form, 'نسيان المفتاح المحفوظ؟ ستحتاج إلى إدخاله من جديد للترجمة.', 'ترجمة المودات', 'YesNo', 'Question', 'Button2',
        [Windows.Forms.MessageBoxOptions]::RtlReading -bor [Windows.Forms.MessageBoxOptions]::RightAlign)
    if ($ok -eq 'Yes') { [void](Remove-FATranslatorKey); Update-KeyState }
})

$btnTranslate.Add_Click({
    if (Test-GameRunning) { Show-Message 'أغلق اللعبة أولاً ثم أعد المحاولة.'; return }
    $key = Get-FATranslatorKey
    $saved = Get-FAProviderChoice
    $args2 = @('-m', 'tools.modpack', 'build')
    if (-not $key) { $args2 += '--offline' }
    Start-Run $args2 $key {
        param($code, $out, $err)
        if ($code -ne 0) {
            $barText.Text = 'فشل البناء.'
            Show-Message ("فشلت الترجمة.`n`n" + (Get-KeyProblem $err))
            return
        }
        $r = $out[-1] | ConvertFrom-Json
        try { $msg = Install-FAPack $r.pack_path } catch { Show-Message ('تعذّر التثبيت: ' + $_.Exception.Message); return }
        Update-Mods; Update-Summary
        $note = ''   # batches that failed leave their strings English: say why instead of a silent "done"
        if ($r.error) { $note = "`n`nتعذّرت ترجمة بعض النصوص فبقيت بالإنجليزية:`n" + (Get-KeyProblem @([string]$r.error)) }
        Show-Message ("تم. $msg`nبالعربية: $(N $r.arabic) من $(N $r.strings) نصاً، وما زال بالإنجليزية: $(N $r.english_left).`nطلبات API في هذا التشغيل: $(N $r.requests)." + $note)
    } ([string]$saved.provider) ([string]$saved.base_url)
    $key = $null
})

$script:ready = $false   # WinForms raises ItemChecked for every item when the list's handle is created: not a click
$form.Add_Shown({ $script:ready = $true })
$list.Add_ItemChecked({
    param($sender, $e)
    if ($script:loading -or -not $script:ready -or -not $e.Item.Tag) { return }
    $name = [string]$e.Item.Tag
    $choice = 'arabic'
    if (-not $e.Item.Checked) { $choice = 'original' }
    $r = Invoke-FAPython @('-m', 'tools.modpack', $choice, $name)
    if ($r.Code -ne 0) { $barText.Text = 'تعذّر حفظ الاختيار: ' + ($r.Output | Select-Object -Last 1); return }
    if ($e.Item.Checked) {
        $e.Item.SubItems[5].Text = 'عربي بعد «ترجمة وتثبيت»'
        $e.Item.SubItems[5].ForeColor = $stateColor.new
    } else {
        $e.Item.SubItems[5].Text = 'أصلي بعد «ترجمة وتثبيت»'
        $e.Item.SubItems[5].ForeColor = $muted
    }
    $barText.Text = 'اضغط «ترجمة وتثبيت» لتطبيق الاختيار. ما تُرجم سابقاً يعود من الذاكرة دون أي طلب.'
})

$btnRefresh.Add_Click({ $form.Cursor = 'WaitCursor'; Update-Mods; Update-Summary; Update-KeyState; $form.Cursor = 'Default' })
$btnReport.Add_Click({ if (Test-Path $reportPath) { Start-Process notepad.exe $reportPath } else { Show-Message 'لا يوجد تقرير بعد: شغّل الترجمة أولاً.' } })
$btnUndo.Add_Click({
    $ok = [Windows.Forms.MessageBox]::Show($form, 'تعطيل حزمة الترجمة ونقلها إلى mods-parked؟ لا يُحذف شيء، والذاكرة تبقى.', 'تراجع', 'YesNo', 'Question', 'Button2',
        [Windows.Forms.MessageBoxOptions]::RtlReading -bor [Windows.Forms.MessageBoxOptions]::RightAlign)
    if ($ok -ne 'Yes') { return }
    try { Show-Message (Uninstall-FAPack $pack) } catch { Show-Message ('تعذّر: ' + $_.Exception.Message) }
})

$form.Add_FormClosing({ if ($script:job -and -not $script:job.Process.HasExited) { $script:job.Process.Kill() } })

# ---------- start ----------
$form.Cursor = 'WaitCursor'
Update-KeyState
Update-Mods
Update-Summary
$form.Cursor = 'Default'

if ($PreviewBusy) {   # for the documentation screenshot of a run in progress
    Set-Busy $true
    $bar.Maximum = 42; $bar.Value = 18
    $barText.Text = "ترجمة النصوص الجديدة: $(N 18) من $(N 42)"
}

if ($Snapshot) {   # for verification: draw the window into an image without showing it
    $updTimer.Stop()
    $deadline = (Get-Date).AddSeconds(15)   # the image shows the real update check, as the window would a moment later
    while ($script:updateCheck -and (Get-Date) -lt $deadline) {
        $u = Get-FAUpdateResult $script:updateCheck
        if ($u) { Show-Updates $u; break }
        Start-Sleep -Milliseconds 100
    }
    $form.Opacity = 0
    $form.Show()
    [Windows.Forms.Application]::DoEvents()   # lets Shown run, as it does in the real message loop
    if ($env:FA_TEST_TOGGLE) {   # automated check of the checkbox handler: untick that mod as a click would
        foreach ($it in $list.Items) { if ($it.Tag -eq $env:FA_TEST_TOGGLE) { $it.Checked = -not $it.Checked } }
    }
    # automated check of the real button flows (background run, exit code, messages): FA_TEST_KEY pastes a key and
    # presses «حفظ وتحقق»; FA_TEST_TRANSLATE then presses «ترجمة وتثبيت». Messages are printed, not shown.
    $clicks = @()
    if ($env:FA_TEST_KEY) { $clicks += 'key' }
    if ($env:FA_TEST_TRANSLATE) { $clicks += 'translate' }
    foreach ($c in $clicks) {
        if ($c -eq 'key') { $keyInput.Text = $env:FA_TEST_KEY; $btnKey.PerformClick() } else { $btnTranslate.PerformClick() }
        $deadline = (Get-Date).AddMinutes(6)
        while ($script:job -and (Get-Date) -lt $deadline) { [Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 100 }
        Write-Output "[$c] bar: $($barText.Text)"
    }
    foreach ($m in $script:messages) { Write-Output "MESSAGE: $m" }
    $form.Refresh()
    $bmp = New-Object Drawing.Bitmap($form.Width, $form.Height)
    $form.DrawToBitmap($bmp, (New-Object Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
    $bmp.Save($Snapshot, [Drawing.Imaging.ImageFormat]::Png)
    $form.Close()
    return
}
[void]$form.ShowDialog()
