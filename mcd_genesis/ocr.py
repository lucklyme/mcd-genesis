"""账单截图 OCR。

走 Windows 内置的 OCR 引擎（WinRT · Windows.Media.Ocr），系统自带简体中文包，
不需要装 tesseract，也不需要任何第三方依赖。

macOS / Linux 或引擎不可用时返回 (False, 原因)，调用方会引导改用文本输入。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from typing import List, Tuple

# PowerShell 通过 WinRT 调用系统 OCR
# 结果一律写入 -OutFile（UTF-8 no BOM）：PowerShell 的 stdout 是系统 OEM 编码，
# 直接用 subprocess 捕获中文必然乱码，走文件最稳。
_PS = r"""
param([string]$Path, [string]$OutFile)
$ErrorActionPreference = 'Stop'
function Save([string]$t) {
    [System.IO.File]::WriteAllText($OutFile, $t, (New-Object System.Text.UTF8Encoding($false)))
}
try {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  # AsTask 扩展方法所在程序集，PowerShell 5.1 需要先显式加载
  Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction SilentlyContinue
  # PowerShell 5.1 必须用 WinRT 类型全称才能解析，否则报「找不到类型」
  $null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
  $null = [Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
  $null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
  $null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
  $null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
  $null = [Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
  $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
      $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
      $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
  })[0]
  function Await($op, $type) {
      $t = $asTaskGeneric.MakeGenericMethod($type).Invoke($null, @($op))
      $t.GetAwaiter().GetResult()
  }

  $file   = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Path)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec    = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp    = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

  $null   = [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
  $lang   = New-Object Windows.Globalization.Language("zh-Hans-CN")
  $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
  if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
  if ($null -eq $engine) { Save "__OCR_NO_ENGINE__"; exit 2 }

  $res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  Save (($res.Lines | ForEach-Object { $_.Text }) -join "`n")
} catch {
  Save ("__OCR_ERROR__" + $_.Exception.Message)
  exit 3
}
"""

# 探测脚本：同样写文件
_PS_PROBE = r"""
param([string]$OutFile)
$ErrorActionPreference = 'Stop'
function Save([string]$t) {
    [System.IO.File]::WriteAllText($OutFile, $t, (New-Object System.Text.UTF8Encoding($false)))
}
try {
  # PowerShell 5.1 必须用 WinRT 类型全称才能解析
  $null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
  $l = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages
  if ($null -eq $l -or $l.Count -eq 0) { Save "__NONE__"; exit 0 }
  Save (($l | ForEach-Object { $_.LanguageTag }) -join ",")
} catch {
  Save ("__OCR_ERROR__" + $_.Exception.Message)
  exit 3
}
"""

_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def _run_ps(script: str, args: List[str]) -> Tuple[int, str]:
    """执行 PowerShell 脚本，结果从临时文件读回（UTF-8）。"""
    fd, ps1 = tempfile.mkstemp(suffix=".ps1")
    os.close(fd)
    outf = ps1 + ".out"
    try:
        with open(ps1, "w", encoding="utf-8-sig") as f:
            f.write(script)
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
               "Bypass", "-File", ps1] + args + ["-OutFile", outf]
        subprocess.run(cmd, capture_output=True, timeout=120)
        if os.path.isfile(outf):
            with open(outf, encoding="utf-8") as f:
                return 0, f.read().strip()
        return 1, ""
    finally:
        for p in (ps1, outf):
            try:
                os.unlink(p)
            except OSError:
                pass


def available() -> Tuple[bool, str]:
    """探测 OCR 可用性。"""
    if not sys.platform.startswith("win"):
        return False, "仅 Windows 可用（调用系统内置 OCR 引擎）"
    try:
        _, out = _run_ps(_PS_PROBE, [])
        if "__NONE__" in out or not out:
            return False, "系统未安装 OCR 语言包"
        if "__OCR_ERROR__" in out:
            return False, "探测失败：" + out.split("__OCR_ERROR__", 1)[1]
        return True, out
    except Exception as e:
        return False, f"探测失败：{e}"


def read(image_path: str) -> Tuple[bool, str, List[str]]:
    """识别一张截图，返回 (是否成功, 全文/原因, 逐行文本)。"""
    if not os.path.isfile(image_path):
        return False, f"找不到图片：{image_path}", []
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in _IMAGE_EXT:
        return False, f"不支持的图片格式：{ext}（支持 {', '.join(sorted(_IMAGE_EXT))}）", []
    if not sys.platform.startswith("win"):
        return False, "截图识别仅支持 Windows", []

    path = os.path.abspath(image_path)
    try:
        _, out = _run_ps(_PS, ["-Path", path])
    except subprocess.TimeoutExpired:
        return False, "识别超时（图片太大？）", []
    except Exception as e:
        return False, f"识别失败：{e}", []

    if "__OCR_NO_ENGINE__" in out:
        return False, "系统没有可用的 OCR 引擎（需要简体中文语言包）", []
    if "__OCR_ERROR__" in out:
        return False, "识别失败：" + out.split("__OCR_ERROR__", 1)[1].strip(), []
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if not lines:
        return False, "图片里没识别出文字（可能是纯图或截图太糊）", []
    return True, "\n".join(lines), lines
