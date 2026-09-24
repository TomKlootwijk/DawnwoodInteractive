@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto native
set "DW_RESIDENT_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_RESIDENT_PYTHON%" goto python
set "DW_RESIDENT_PYTHON=python"
:python
"%DW_RESIDENT_PYTHON%" -X utf8 -B local_lab\source_resident.py %*
exit /b %errorlevel%
:native
"Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3\Dawnwood_GPU_v0.3\bin\windows-resident\dawnwood-resident.exe" %*
exit /b %errorlevel%
