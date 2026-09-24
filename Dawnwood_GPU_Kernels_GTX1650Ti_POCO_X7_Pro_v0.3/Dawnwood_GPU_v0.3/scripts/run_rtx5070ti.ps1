param(
    [string]$Binary = "$PSScriptRoot/../bin/windows-rtx5070ti/dawnwood.exe",
    [uint32]$Count = 1048576,
    [uint32]$Steps = 64,
    [string]$Output = '',
    [string]$Checkpoint = ''
)
$ErrorActionPreference = 'Stop'
$arguments = @('run','--device','RTX 5070 Ti','--stream','--count',"$Count",'--steps',"$Steps",'--batch','8','--budget-fraction','0.98')
if ($Output) { $arguments += @('--out',$Output) }
if ($Checkpoint) { $arguments += @('--checkpoint',$Checkpoint) }
& $Binary @arguments
if ($LASTEXITCODE -ne 0) { throw "Dawnwood exited with code $LASTEXITCODE" }
