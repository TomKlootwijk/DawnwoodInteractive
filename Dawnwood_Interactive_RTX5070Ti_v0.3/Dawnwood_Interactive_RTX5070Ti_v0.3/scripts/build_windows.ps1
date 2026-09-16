# Run from ordinary PowerShell with Visual Studio 2022 C++ Build Tools,
# CMake and CUDA >=12.8 installed. Existing CMake generators are preserved.
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
param([string]$BuildDirectory = 'build')

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$taskBuildPath = if ([IO.Path]::IsPathRooted($BuildDirectory)) {
    [IO.Path]::GetFullPath($BuildDirectory)
} else {
    [IO.Path]::GetFullPath((Join-Path $Root $BuildDirectory))
}

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    $taskVswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path -LiteralPath $taskVswhere -PathType Leaf)) {
        throw 'Install Visual Studio 2022 Build Tools with the C++ build tools component, or run from its Developer PowerShell.'
    }
    $taskVsInstall = & $taskVswhere -latest -products '*' -version '[17.0,18.0)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($LASTEXITCODE -ne 0 -or -not $taskVsInstall) {
        throw 'Visual Studio 2022 with Microsoft.VisualStudio.Component.VC.Tools.x86.x64 was not found.'
    }
    $taskVcvars = Join-Path ($taskVsInstall | Select-Object -First 1) 'VC\Auxiliary\Build\vcvars64.bat'
    if (-not (Test-Path -LiteralPath $taskVcvars -PathType Leaf)) {
        throw "Missing x64 compiler environment script: $taskVcvars"
    }
    # Import only NAME=VALUE output into this process; never evaluate it as code.
    $taskEnvironment = & $env:ComSpec /d /c ('call "{0}" >nul && set' -f $taskVcvars)
    if ($LASTEXITCODE -ne 0) { throw "Failed to initialize MSVC using $taskVcvars" }
    foreach ($taskEntry in $taskEnvironment) {
        $taskSeparator = $taskEntry.IndexOf('=')
        if ($taskSeparator -gt 0) {
            [Environment]::SetEnvironmentVariable($taskEntry.Substring(0, $taskSeparator), $taskEntry.Substring($taskSeparator + 1), 'Process')
        }
    }
    if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
        throw 'The x64 MSVC environment did not provide cl.exe.'
    }
    Write-Host "Imported x64 MSVC environment: $taskVsInstall"
}

$taskCache = Join-Path $taskBuildPath 'CMakeCache.txt'
$taskGenerator = $null
if (Test-Path -LiteralPath $taskCache -PathType Leaf) {
    $taskGeneratorLine = Get-Content -LiteralPath $taskCache | Select-String '^CMAKE_GENERATOR:INTERNAL=(.+)$' | Select-Object -First 1
    if ($taskGeneratorLine) { $taskGenerator = $taskGeneratorLine.Matches[0].Groups[1].Value }
}
$taskExistingGenerator = [bool]$taskGenerator
if (-not $taskGenerator) {
    $taskGenerator = if (Get-Command ninja.exe -ErrorAction SilentlyContinue) { 'Ninja' } else { 'Visual Studio 17 2022' }
}
$taskConfigure = @('-S', $Root, '-B', $taskBuildPath, '-G', $taskGenerator, '-DCMAKE_BUILD_TYPE=Release', '-DDW_ENABLE_CUDA=ON', '-DCMAKE_CUDA_ARCHITECTURES=120-real;120-virtual')
# -A is unsupported by Ninja. Existing Visual Studio caches already specify
# their platform; do not replace it with a conflicting architecture argument.
if (-not $taskExistingGenerator -and $taskGenerator -like 'Visual Studio *') {
    $taskConfigure += @('-A', 'x64')
}
Write-Host "Generator: $taskGenerator | Configuration: Release | Build: $taskBuildPath"
Push-Location $Root
try {
    & cmake @taskConfigure
    if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed' }
    & cmake --build $taskBuildPath --config Release --parallel 3
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    & ctest --test-dir $taskBuildPath -C Release --output-on-failure -LE gpu
    if ($LASTEXITCODE -ne 0) { throw 'CPU tests failed' }
    $taskExecutablePath = if ($taskGenerator -like 'Visual Studio *' -or $taskGenerator -like '*Multi-Config*') { Join-Path $taskBuildPath 'Release' } else { $taskBuildPath }
    Write-Host "Built optimized: $(Join-Path $taskExecutablePath 'dawnwood.exe')"
    Write-Host "Built reference: $(Join-Path $taskExecutablePath 'dawnwood_reference.exe')"
    Write-Host "Built integer edition: $(Join-Path $taskExecutablePath 'dawnwood_integer.exe')"
    Write-Host "Built direct texture edition: $(Join-Path $taskExecutablePath 'dawnwood_integer_texture.exe')"
    Write-Host "CPU tests passed. GPU check: & '$(Join-Path $taskExecutablePath 'dawnwood.exe')' --self-test"
} finally { Pop-Location }
