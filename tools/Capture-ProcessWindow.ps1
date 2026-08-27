[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int] $ProcessId,

    [Parameter(Mandatory = $true)]
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Add-Type -AssemblyName System.Drawing

if (-not ('Fable2Calibration.WindowCapture' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

namespace Fable2Calibration {
    public static class WindowCapture {
        [StructLayout(LayoutKind.Sequential)]
        public struct Rect {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool GetWindowRect(IntPtr window, out Rect rect);
    }
}
'@
}

$process = Get-Process -Id $ProcessId -ErrorAction Stop
$process.Refresh()
$window = $process.MainWindowHandle
if ($window -eq [IntPtr]::Zero) {
    throw "Process $ProcessId does not have a main window."
}

$rect = [Fable2Calibration.WindowCapture+Rect]::new()
if (-not [Fable2Calibration.WindowCapture]::GetWindowRect($window, [ref]$rect)) {
    throw "GetWindowRect failed for process $ProcessId."
}

$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
    throw "Process $ProcessId has an invalid window rectangle: ${width}x${height}."
}

$resolvedOutputPath = [IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

$bitmap = [Drawing.Bitmap]::new($width, $height)
$graphics = [Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.CopyFromScreen(
        $rect.Left,
        $rect.Top,
        0,
        0,
        [Drawing.Size]::new($width, $height),
        [Drawing.CopyPixelOperation]::SourceCopy)
    $bitmap.Save($resolvedOutputPath, [Drawing.Imaging.ImageFormat]::Png)
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}

[pscustomobject]@{
    ProcessId = $ProcessId
    Window = '0x{0:X}' -f $window.ToInt64()
    Width = $width
    Height = $height
    OutputPath = $resolvedOutputPath
}
