param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Compiler,
    [Parameter(Mandatory=$true)][string]$VulkanSDK,
    [Parameter(Mandatory=$true)][string]$Binary,
    [Parameter(Mandatory=$true)][string]$Evidence,
    [Parameter(Mandatory=$true)][string]$Name
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$native = Join-Path $root 'Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3/Dawnwood_GPU_v0.3'
if (!(Test-Path (Join-Path $native 'CMakeLists.txt'))) { $native = Join-Path $root 'kernel' }
if (!(Test-Path (Join-Path $native 'CMakeLists.txt'))) { throw 'Cannot locate the Dawnwood kernel source' }
$recorder = Join-Path $PSScriptRoot 'record_gpu_run.py'
$savedPath = $env:PATH
$env:PATH = (Join-Path $VulkanSDK 'Bin') + ';' + $env:PATH
New-Item -ItemType Directory -Force (Split-Path $Binary -Parent) | Out-Null
Push-Location $native
try {
    & $Python -B $recorder --out $Evidence --name ($Name + '_shaders') -- $Python -B tools/build_shaders.py --optimize --preserve-math-functions --preserve-interpreter-functions
    if ($LASTEXITCODE -ne 0) { throw 'Shader build failed; see recorded stderr' }
    $arguments = @('-std=c++17','-O2','-ffp-contract=off','-fno-fast-math','-static','-I','include','-I',(Join-Path $VulkanSDK 'Include'),'src/main.cpp','src/cpu.cpp','src/vulkan.cpp','src/driver.cpp',(Join-Path $VulkanSDK 'Lib/vulkan-1.lib'),'-o',$Binary)
    & $Python -B $recorder --out $Evidence --name ($Name + '_native') -- $Compiler @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Native build failed; see recorded stderr' }
} finally {
    Pop-Location
    $env:PATH = $savedPath
}
