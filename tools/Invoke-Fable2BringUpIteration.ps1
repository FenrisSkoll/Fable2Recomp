[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 1000)]
    [int] $Iteration,

    [Parameter(Mandatory = $true)]
    [string] $RunDirectory,

    [string] $BuildPreset = 'win-amd64-release',

    [ValidateRange(1, 3600)]
    [int] $MonitorSeconds = 60,

    [string] $FaultWalkReportPath = '',

    [switch] $SkipCodegen,

    [switch] $SkipBuild,

    [switch] $ManualInput,

    [switch] $GracefulStop
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Get-Fable2NextRunNumber {
    param(
        [Parameter(Mandatory = $true)]
        [string] $RepositoryRoot
    )

    $highestRunNumber = 0
    $existingLogs = Get-ChildItem `
        -LiteralPath $RepositoryRoot `
        -Filter 'fable2-run-*.log' `
        -File

    foreach ($existingLog in $existingLogs) {
        if ($existingLog.BaseName -notmatch '^fable2-run-(\d+)$') {
            continue
        }

        $existingRunNumber = [int] $Matches[1]
        if ($existingRunNumber -gt $highestRunNumber) {
            $highestRunNumber = $existingRunNumber
        }
    }

    return $highestRunNumber + 1
}

$manifestPath = Join-Path $repositoryRoot 'fable2_manifest.toml'
$buildDirectory = Join-Path $repositoryRoot "out\build\$BuildPreset"
$executablePath = Join-Path $buildDirectory 'fable2.exe'
$inputHelperPath = Join-Path $repositoryRoot 'out\input-calibration\Send-Fable2Key.ps1'
$gameDataRoot = Join-Path $repositoryRoot 'assets\runtime'
$updateDataRoot = Join-Path $repositoryRoot 'assets\update'
$resolvedRunDirectory = [IO.Path]::GetFullPath($RunDirectory)
$iterationName = 'iteration-{0:D2}' -f $Iteration
$iterationDirectory = Join-Path $resolvedRunDirectory $iterationName
$codegenLogPath = Join-Path $repositoryRoot 'fable2-codegen.log'
$buildLogPath = Join-Path $repositoryRoot 'fable2-build.log'
$runNumber = Get-Fable2NextRunNumber -RepositoryRoot $repositoryRoot
$runText = '{0:D3}' -f $runNumber
$runtimeLogName = "fable2-run-$runText.log"
$runtimeLogPath = Join-Path $repositoryRoot $runtimeLogName
$runtimeLogArgument = ".\$runtimeLogName"
$guestDumpPath = Join-Path $iterationDirectory 'tu1-text-0x82000000.bin'
$resultPath = Join-Path $iterationDirectory 'result.json'
$summaryPath = Join-Path $resolvedRunDirectory 'run-summary.md'
$guestDumpStart = [Convert]::ToUInt32('82000000', 16)
$guestDumpLength = [Convert]::ToUInt32('01300000', 16)

New-Item -ItemType Directory -Force -Path $iterationDirectory | Out-Null

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Manifest was not found: $manifestPath"
}

if (-not (Test-Path -LiteralPath $inputHelperPath -PathType Leaf)) {
    throw "The calibrated input helper was not found: $inputHelperPath"
}

if (Test-Path -LiteralPath $runtimeLogPath) {
    throw "The resolved numbered runtime log already exists: $runtimeLogPath"
}

if (-not ('Fable2BringUp.NativeMethods' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

namespace Fable2BringUp {
    public static class NativeMethods {
        private const uint PROCESS_VM_READ = 0x0010;
        private const uint PROCESS_QUERY_INFORMATION = 0x0400;
        private const int SW_RESTORE = 9;
        private const uint INPUT_KEYBOARD = 1;
        private const uint KEYEVENTF_EXTENDEDKEY = 0x0001;
        private const uint KEYEVENTF_KEYUP = 0x0002;
        private const uint KEYEVENTF_SCANCODE = 0x0008;

        private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential)]
        private struct INPUT {
            public uint type;
            public InputUnion union;
        }

        // INPUT's native union is 32 bytes on 64-bit Windows because its
        // largest member is MOUSEINPUT. SendInput rejects a smaller cbSize.
        [StructLayout(LayoutKind.Explicit, Size = 32)]
        private struct InputUnion {
            [FieldOffset(0)]
            public KEYBDINPUT keyboard;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct KEYBDINPUT {
            public ushort virtualKey;
            public ushort scanCode;
            public uint flags;
            public uint time;
            public UIntPtr extraInfo;
        }

        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);

        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern bool BringWindowToTop(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hwnd, int command);

        [DllImport("user32.dll")]
        private static extern IntPtr SetFocus(IntPtr hwnd);

        [DllImport("user32.dll")]
        private static extern bool AttachThreadInput(uint attach, uint attachTo, bool attachState);

        [DllImport("kernel32.dll")]
        private static extern uint GetCurrentThreadId();

        [DllImport("user32.dll", SetLastError = true)]
        private static extern uint SendInput(uint inputCount, INPUT[] inputs, int inputSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(uint desiredAccess, bool inheritHandle, uint processId);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool ReadProcessMemory(
            IntPtr process,
            IntPtr baseAddress,
            byte[] buffer,
            UIntPtr size,
            out UIntPtr bytesRead);

        [DllImport("kernel32.dll")]
        private static extern bool CloseHandle(IntPtr handle);

        private static IntPtr FindWindow(uint processId) {
            IntPtr result = IntPtr.Zero;
            EnumWindows(delegate(IntPtr hwnd, IntPtr state) {
                uint ownerProcessId;
                GetWindowThreadProcessId(hwnd, out ownerProcessId);
                if (ownerProcessId == processId && IsWindowVisible(hwnd)) {
                    result = hwnd;
                    return false;
                }
                return true;
            }, IntPtr.Zero);
            return result;
        }

        public static IntPtr WaitForWindow(uint processId, int timeoutMilliseconds) {
            Stopwatch stopwatch = Stopwatch.StartNew();
            while (stopwatch.ElapsedMilliseconds < timeoutMilliseconds) {
                IntPtr hwnd = FindWindow(processId);
                if (hwnd != IntPtr.Zero) {
                    return hwnd;
                }
                Thread.Sleep(100);
            }
            return IntPtr.Zero;
        }

        public static bool ActivateWindow(uint processId, out IntPtr window) {
            window = FindWindow(processId);
            if (window == IntPtr.Zero) {
                return false;
            }

            ShowWindow(window, SW_RESTORE);
            IntPtr foreground = GetForegroundWindow();
            uint foregroundThread = foreground == IntPtr.Zero
                ? 0
                : GetWindowThreadProcessId(foreground, out _);
            uint currentThread = GetCurrentThreadId();
            bool attached = foregroundThread != 0 && foregroundThread != currentThread
                && AttachThreadInput(currentThread, foregroundThread, true);

            try {
                BringWindowToTop(window);
                SetForegroundWindow(window);
                SetFocus(window);
            } finally {
                if (attached) {
                    AttachThreadInput(currentThread, foregroundThread, false);
                }
            }

            Thread.Sleep(100);
            IntPtr actualForeground = GetForegroundWindow();
            uint actualProcessId;
            GetWindowThreadProcessId(actualForeground, out actualProcessId);
            return actualProcessId == processId;
        }

        public static void PressScanCode(ushort scanCode, bool extended) {
            uint baseFlags = KEYEVENTF_SCANCODE | (extended ? KEYEVENTF_EXTENDEDKEY : 0);
            INPUT[] inputs = new INPUT[2];
            inputs[0].type = INPUT_KEYBOARD;
            inputs[0].union.keyboard.scanCode = scanCode;
            inputs[0].union.keyboard.flags = baseFlags;
            inputs[1].type = INPUT_KEYBOARD;
            inputs[1].union.keyboard.scanCode = scanCode;
            inputs[1].union.keyboard.flags = baseFlags | KEYEVENTF_KEYUP;

            uint sent = SendInput((uint)inputs.Length, inputs, Marshal.SizeOf<INPUT>());
            if (sent != inputs.Length) {
                throw new Win32Exception(Marshal.GetLastWin32Error(),
                    "SendInput did not inject the complete key press");
            }
        }

        private static bool TryRead(
            IntPtr process,
            ulong address,
            byte[] buffer,
            out int bytesRead) {
            UIntPtr nativeBytesRead;
            bool success = ReadProcessMemory(
                process,
                new IntPtr(unchecked((long)address)),
                buffer,
                new UIntPtr((uint)buffer.Length),
                out nativeBytesRead);
            bytesRead = checked((int)nativeBytesRead.ToUInt64());
            return success && bytesRead == buffer.Length;
        }

        public static bool DumpGuestRange(
            uint processId,
            uint guestStart,
            uint length,
            string outputPath,
            out ulong mappingBase,
            out uint readableBytes) {
            mappingBase = 0;
            readableBytes = 0;
            IntPtr process = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, false, processId);
            if (process == IntPtr.Zero) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "OpenProcess failed");
            }

            try {
                byte[] knownInstruction = new byte[4];
                for (int bit = 32; bit < 47; ++bit) {
                    ulong candidateBase = 1UL << bit;
                    int count;
                    if (TryRead(process, candidateBase + 0x82267510UL, knownInstruction, out count)
                        && knownInstruction[0] == 0x7D
                        && knownInstruction[1] == 0x88
                        && knownInstruction[2] == 0x02
                        && knownInstruction[3] == 0xA6) {
                        mappingBase = candidateBase;
                        break;
                    }
                }

                if (mappingBase == 0) {
                    return false;
                }

                const int chunkSize = 0x10000;
                byte[] chunk = new byte[chunkSize];
                using (FileStream output = new FileStream(outputPath, FileMode.Create, FileAccess.Write, FileShare.Read)) {
                    uint offset = 0;
                    while (offset < length) {
                        int currentSize = (int)Math.Min((uint)chunkSize, length - offset);
                        if (chunk.Length != currentSize) {
                            chunk = new byte[currentSize];
                        } else {
                            Array.Clear(chunk, 0, chunk.Length);
                        }

                        int count;
                        bool success = TryRead(process, mappingBase + guestStart + offset, chunk, out count);
                        if (success) {
                            readableBytes += (uint)count;
                        }
                        output.Write(chunk, 0, chunk.Length);
                        offset += (uint)chunk.Length;
                    }
                }
                return true;
            } finally {
                CloseHandle(process);
            }
        }
    }
}
'@
}

function Write-Result {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable] $Result
    )

    $Result['iteration'] = $Iteration
    $Result['iteration_directory'] = $iterationDirectory
    $Result['codegen_log'] = $codegenLogPath
    $Result['build_log'] = $buildLogPath
    $Result['runtime_log'] = $runtimeLogPath
    $Result['guest_dump'] = $guestDumpPath
    $Result['result_path'] = $resultPath
    $Result['completed_at'] = [DateTimeOffset]::Now.ToString('o')

    $json = $Result | ConvertTo-Json -Depth 8
    Set-Content -LiteralPath $resultPath -Value $json -Encoding utf8

    if (-not (Test-Path -LiteralPath $summaryPath)) {
        Set-Content -LiteralPath $summaryPath -Encoding utf8 -Value @(
            '# Fable II TU1 bring-up run'
            ''
            "Run directory: $resolvedRunDirectory"
            ''
        )
    }

    $fatalText = if ($Result.ContainsKey('fatal_line')) { $Result['fatal_line'] } else { '' }
    $guardrailText = if ($Result.ContainsKey('fault_walk_guardrail_line')) {
        $Result['fault_walk_guardrail_line']
    } else {
        ''
    }
    Add-Content -LiteralPath $summaryPath -Encoding utf8 -Value @(
        "## Iteration $Iteration"
        ''
        "- Classification: $($Result['classification'])"
        "- Runtime log: $runtimeLogPath"
        "- Fatal: $fatalText"
        "- Fault-walk guardrail: $guardrailText"
        "- Input events: $($Result['input_events'] -join '; ')"
        ''
    )

    Write-Output "RESULT_PATH=$resultPath"
    Write-Output "CLASSIFICATION=$($Result['classification'])"
    if ($Result.ContainsKey('fatal_line')) {
        Write-Output "FATAL_LINE=$($Result['fatal_line'])"
    }
    if ($Result.ContainsKey('fault_walk_guardrail_line')) {
        Write-Output "FAULT_WALK_GUARDRAIL_LINE=$($Result['fault_walk_guardrail_line'])"
    }
}

function Get-FirstFatalLine {
    if (-not (Test-Path -LiteralPath $runtimeLogPath -PathType Leaf)) {
        return $null
    }

    return Get-Content -LiteralPath $runtimeLogPath |
        Where-Object { $_ -match '\[FATAL\]' } |
        Select-Object -First 1
}

function Get-FirstFaultWalkGuardrailLine {
    if (-not (Test-Path -LiteralPath $runtimeLogPath -PathType Leaf)) {
        return $null
    }

    return Get-Content -LiteralPath $runtimeLogPath |
        Where-Object { $_ -match '\[FWT\] GUARDRAIL STOP:' } |
        Select-Object -First 1
}

function Test-ProcessStopped {
    param(
        [Parameter(Mandatory = $true)]
        [Diagnostics.Process] $Process
    )

    try {
        return $Process.HasExited
    } catch {
        return $true
    }
}

function Stop-ExactProcess {
    param(
        [Parameter(Mandatory = $true)]
        [Diagnostics.Process] $Process
    )

    if (-not (Test-ProcessStopped -Process $Process)) {
        Stop-Process -Id $Process.Id -Force
        $Process.WaitForExit(5000) | Out-Null
    }
}

function Get-ExitCodeHex {
    param(
        [Parameter(Mandatory = $true)]
        [Diagnostics.Process] $Process
    )

    if (-not (Test-ProcessStopped -Process $Process)) {
        return $null
    }

    $exitCodeBytes = [BitConverter]::GetBytes([int32]$Process.ExitCode)
    $unsignedExitCode = [BitConverter]::ToUInt32($exitCodeBytes, 0)
    return '0x{0:X8}' -f $unsignedExitCode
}

function Invoke-InputPress {
    param(
        [Parameter(Mandatory = $true)]
        [Diagnostics.Process] $Process,

        [Parameter(Mandatory = $true)]
        [ValidateSet('A', 'DPadLeft')]
        [string] $Key,

        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [Collections.Generic.List[string]] $InputEvents
    )

    if (Test-ProcessStopped -Process $Process) {
        throw "The game process exited before $Name could be sent."
    }

    $inputResult = & $inputHelperPath `
        -ProcessId $Process.Id `
        -Key $Key `
        -HoldMilliseconds 150

    if (-not $inputResult.ForegroundVerified) {
        throw "The calibrated helper did not verify foreground activation before sending $Name."
    }

    $InputEvents.Add(('{0:o} {1} key={2} hold_ms=150 foreground_verified=true' -f `
        [DateTimeOffset]::Now,
        $Name,
        $Key))
}

$result = @{
    classification = 'Unknown'
    build_preset = $BuildPreset
    input_events = [Collections.Generic.List[string]]::new()
    run_number = $runText
    started_at = [DateTimeOffset]::Now.ToString('o')
}

if ($SkipCodegen) {
    Write-Output "[$iterationName] Reusing existing generated code"
    $codegenExitCode = 0
    $result['codegen_skipped'] = $true
} else {
    Write-Output "[$iterationName] ReXGlue codegen via $BuildPreset"
    Push-Location $repositoryRoot
    try {
        & cmake --build --preset $BuildPreset --target fable2_codegen 2>&1 |
            Tee-Object -FilePath $codegenLogPath
        $codegenExitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

$result['codegen_exit_code'] = $codegenExitCode
if ($codegenExitCode -ne 0) {
    $result['classification'] = 'CodegenFailure'
    Write-Result -Result $result
    exit 20
}

if ($SkipBuild) {
    Write-Output "[$iterationName] Reusing existing $BuildPreset executable"
    $buildExitCode = 0
    $result['build_skipped'] = $true
} else {
    Write-Output "[$iterationName] Build $BuildPreset"
    Push-Location $repositoryRoot
    try {
        & cmake --build --preset $BuildPreset 2>&1 | Tee-Object -FilePath $buildLogPath
        $buildExitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

$result['build_exit_code'] = $buildExitCode
if ($buildExitCode -ne 0) {
    $result['classification'] = 'BuildFailure'
    Write-Result -Result $result
    exit 21
}

if (-not (Test-Path -LiteralPath $executablePath -PathType Leaf)) {
    $result['classification'] = 'BuildOutputMissing'
    Write-Result -Result $result
    exit 22
}

$processStartInfo = [Diagnostics.ProcessStartInfo]::new()
$processStartInfo.FileName = $executablePath
$processStartInfo.WorkingDirectory = $repositoryRoot
$processStartInfo.UseShellExecute = $false
$processStartInfo.ArgumentList.Add('--game_data_root')
$processStartInfo.ArgumentList.Add('.\assets\runtime')
$processStartInfo.ArgumentList.Add('--update_data_root')
$processStartInfo.ArgumentList.Add('.\assets\update')
$processStartInfo.ArgumentList.Add('--gpu_plugin=xenos')
$processStartInfo.ArgumentList.Add('--log_level')
$processStartInfo.ArgumentList.Add('debug')
$processStartInfo.ArgumentList.Add('--mnk_mode')
$processStartInfo.ArgumentList.Add('--log_file')
$processStartInfo.ArgumentList.Add($runtimeLogArgument)
if ($FaultWalkReportPath) {
    $resolvedFaultWalkReportPath = [IO.Path]::GetFullPath($FaultWalkReportPath)
    $faultWalkReportDirectory = Split-Path -Parent $resolvedFaultWalkReportPath
    New-Item -ItemType Directory -Force -Path $faultWalkReportDirectory | Out-Null
    $processStartInfo.Environment['REXGLUE_FAULT_WALK_REPORT'] = $resolvedFaultWalkReportPath
    $result['fault_walk_report'] = $resolvedFaultWalkReportPath
}

$gameProcess = [Diagnostics.Process]::new()
$gameProcess.StartInfo = $processStartInfo
$launchStopwatch = [Diagnostics.Stopwatch]::StartNew()
if (-not $gameProcess.Start()) {
    $result['classification'] = 'LaunchFailure'
    Write-Result -Result $result
    exit 23
}

$result['process_id'] = $gameProcess.Id
$result['launch_arguments'] = @(
    '--game_data_root'
    '.\assets\runtime'
    '--update_data_root'
    '.\assets\update'
    '--gpu_plugin=xenos'
    '--log_level'
    'debug'
    '--mnk_mode'
    '--log_file'
    $runtimeLogArgument
)

Write-Output "[$iterationName] Launched PID $($gameProcess.Id); waiting 19 seconds"

$dumpCompleted = $false
$mappingBase = [uint64]0
$readableBytes = [uint32]0
while ($launchStopwatch.Elapsed.TotalSeconds -lt 18.5) {
    if (Test-ProcessStopped -Process $gameProcess) {
        break
    }

    if (-not $dumpCompleted -and $launchStopwatch.Elapsed.TotalSeconds -ge 1) {
        $dumpCompleted = [Fable2BringUp.NativeMethods]::DumpGuestRange(
            [uint32]$gameProcess.Id,
            $guestDumpStart,
            $guestDumpLength,
            $guestDumpPath,
            [ref]$mappingBase,
            [ref]$readableBytes)
        if ($dumpCompleted) {
            $result['guest_mapping_base'] = '0x{0:X}' -f $mappingBase
            $result['guest_dump_readable_bytes'] = $readableBytes
            $result['guest_dump_sha256'] = (Get-FileHash -LiteralPath $guestDumpPath -Algorithm SHA256).Hash
            Write-Output "[$iterationName] Captured TU1-patched guest bytes from mapping base 0x$($mappingBase.ToString('X'))"
        }
    }

    Start-Sleep -Milliseconds 100
}

$remainingMilliseconds = [Math]::Ceiling(19000 - $launchStopwatch.Elapsed.TotalMilliseconds)
if ($remainingMilliseconds -gt 0) {
    Start-Sleep -Milliseconds $remainingMilliseconds
}

if ($ManualInput) {
    $result['manual_input'] = $true
    Write-Output "[$iterationName] Manual input enabled; monitoring for $MonitorSeconds seconds"
} else {
    try {
        Invoke-InputPress -Process $gameProcess -Key A -Name 'Space (Xbox A) #1' -InputEvents $result['input_events']
        Start-Sleep -Milliseconds 1500
        Invoke-InputPress -Process $gameProcess -Key A -Name 'Space (Xbox A) #2' -InputEvents $result['input_events']
        Start-Sleep -Milliseconds 1500
        Invoke-InputPress -Process $gameProcess -Key A -Name 'Space (Xbox A) #3' -InputEvents $result['input_events']
        # The hero-selection UI was still neutral when Left was sent after 1.5 seconds.
        # Six seconds was visually validated by the dedicated D-Pad calibration.
        Start-Sleep -Seconds 6
        Invoke-InputPress -Process $gameProcess -Key DPadLeft -Name 'Left Arrow (D-Pad Left)' -InputEvents $result['input_events']
        Start-Sleep -Milliseconds 1500
        Invoke-InputPress -Process $gameProcess -Key A -Name 'Space (Xbox A) #4' -InputEvents $result['input_events']
    } catch {
        $result['classification'] = if (Test-ProcessStopped -Process $gameProcess) {
            'ProcessExitedDuringInput'
        } else {
            'InputAutomationFailure'
        }
        $result['input_error'] = $_.Exception.Message
        $result['exit_code'] = Get-ExitCodeHex -Process $gameProcess
        $fatalLine = Get-FirstFatalLine
        if ($null -ne $fatalLine) {
            $result['fatal_line'] = $fatalLine
        }
        Stop-ExactProcess -Process $gameProcess
        Write-Result -Result $result
        exit 24
    }

    $result['final_input_at'] = [DateTimeOffset]::Now.ToString('o')
    Write-Output "[$iterationName] Final Space sent; monitoring for $MonitorSeconds seconds"
}

$monitorStopwatch = [Diagnostics.Stopwatch]::StartNew()

while ($monitorStopwatch.Elapsed.TotalSeconds -lt $MonitorSeconds) {
    $fatalLine = Get-FirstFatalLine
    if ($null -ne $fatalLine) {
        $result['fatal_line'] = $fatalLine
        if ($fatalLine -match 'Call to invalid or unregistered function:\s*target=(0x[0-9A-Fa-f]+),\s*ctx\.lr=(0x[0-9A-Fa-f]+),\s*probable caller=(0x[0-9A-Fa-f]+),\s*ctx\.ctr=(0x[0-9A-Fa-f]+)') {
            $result['classification'] = 'InvalidUnregisteredFunction'
            $result['fatal_target'] = $Matches[1].ToUpperInvariant().Replace('0X', '0x')
            $result['lr'] = $Matches[2].ToUpperInvariant().Replace('0X', '0x')
            $result['probable_caller'] = $Matches[3].ToUpperInvariant().Replace('0X', '0x')
            $result['ctr'] = $Matches[4].ToUpperInvariant().Replace('0X', '0x')
        } else {
            $result['classification'] = 'OtherFatal'
        }
        break
    }

    $faultWalkGuardrailLine = Get-FirstFaultWalkGuardrailLine
    if ($null -ne $faultWalkGuardrailLine) {
        $result['classification'] = 'FaultWalkGuardrail'
        $result['fault_walk_guardrail_line'] = $faultWalkGuardrailLine
        break
    }

    if (Test-ProcessStopped -Process $gameProcess) {
        $result['classification'] = 'ProcessExited'
        $result['exit_code'] = Get-ExitCodeHex -Process $gameProcess
        break
    }

    Start-Sleep -Milliseconds 250
}

if ($result['classification'] -eq 'Unknown') {
    $result['classification'] = 'PostInputTimeout'
}

if ($GracefulStop -and -not (Test-ProcessStopped -Process $gameProcess)) {
    $result['graceful_stop_requested'] = $gameProcess.CloseMainWindow()
    if ($result['graceful_stop_requested']) {
        $gameProcess.WaitForExit(5000) | Out-Null
    }
}

Stop-ExactProcess -Process $gameProcess
if (-not $result.ContainsKey('exit_code')) {
    $result['exit_code'] = Get-ExitCodeHex -Process $gameProcess
}

Write-Result -Result $result
exit 0
