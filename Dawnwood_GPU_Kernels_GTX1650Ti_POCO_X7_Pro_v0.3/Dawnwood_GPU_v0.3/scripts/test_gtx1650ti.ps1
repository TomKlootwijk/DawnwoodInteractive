param(
    [string]$Binary = "$PSScriptRoot/../build/Release/dawnwood.exe",
    [string]$Output = "$PSScriptRoot/../results/gtx1650ti_local"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $Output | Out-Null
function Invoke-Dawnwood([string]$File, [string[]]$Arguments) {
    $text = & $Binary @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Dawnwood failed: $($Arguments -join ' ')" }
    $text | Set-Content -Encoding UTF8 -Path (Join-Path $Output $File)
}
Invoke-Dawnwood "cpu_selftest.json" @("selftest")
Invoke-Dawnwood "device.json" @("probe", "--device", "1650 Ti")
Invoke-Dawnwood "cpu_gpu_comparison.json" @("verify", "--device", "1650 Ti", "--count", "128", "--steps", "16")
Invoke-Dawnwood "numerical_session.json" @("run", "--backend", "vulkan", "--device", "1650 Ti", "--count", "4096", "--steps", "64", "--batch", "8", "--checkpoint", (Join-Path $Output "working_state.dwk"))
Write-Output "Saved real-device results to $Output"
