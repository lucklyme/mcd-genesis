# 生成一张示例麦当劳账单图片，用于验证「截图 → OCR → 捏人」链路。
# 仅用于测试，不需要麦当劳的真实小票。
#
# powershell -ExecutionPolicy Bypass -File examples/make_receipt.ps1 -Out examples/receipt-sample.png
param([string]$Out = "examples/receipt-sample.png")

Add-Type -AssemblyName System.Drawing

# 显式加载字体文件，避免系统字体回退导致中文渲染成方块
$fontFile = "C:\Windows\Fonts\msyh.ttc"
if (-not (Test-Path $fontFile)) { $fontFile = "C:\Windows\Fonts\msyh.ttf" }
$pc = New-Object System.Drawing.Text.PrivateFontCollection
if (Test-Path $fontFile) { $pc.AddFontFile($fontFile) }
$ff = if ($pc.Families.Count -gt 0) { $pc.Families[0] } else { (New-Object System.Drawing.Font("Microsoft YaHei", 14)).FontFamily }

$w = 560; $h = 480
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g   = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

$title = New-Object System.Drawing.Font($ff, 17, [System.Drawing.FontStyle]::Bold)
$body  = New-Object System.Drawing.Font($ff, 14)
$black = [System.Drawing.Brushes]::Black
$gray  = [System.Drawing.Brushes]::DimGray
$pen   = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(60,60,60))

$y = 28
$g.DrawString("麦当劳  上海人民广场餐厅", $title, $black, 34, $y); $y += 34
$g.DrawString("2026-10-16  12:41     堂食", $body, $gray, 34, $y);   $y += 30
$g.DrawLine($pen, 34, $y, $w - 34, $y); $y += 14

$items = @(
    "巨无霸              x2    51.00",
    "麦乐鸡5块           x1    13.00",
    "大薯条              x1    12.00",
    "草莓麦旋风          x1     9.50",
    "可乐中杯            x1     8.50"
)
foreach ($it in $items) {
    $g.DrawString($it, $body, $black, 34, $y); $y += 34
}

$g.DrawLine($pen, 34, $y, $w - 34, $y); $y += 14
$g.DrawString("合计  6 件            118.00", $title, $black, 34, $y); $y += 40
$g.DrawString("谢谢惠顾  欢迎再次光临", $body, $gray, 34, $y)

$g.Dispose()
$dir = Split-Path -Parent $Out
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
$bmp.Save((Resolve-Path -Path $dir).Path + "\" + (Split-Path -Leaf $Out), [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "saved: $Out"
