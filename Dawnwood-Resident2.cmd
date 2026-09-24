@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto native
set "DW_RESIDENT2_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_RESIDENT2_PYTHON%" goto python
set "DW_RESIDENT2_PYTHON=python"
:python
"%DW_RESIDENT2_PYTHON%" -X utf8 -B local_lab\source_resident_v2.py %*
exit /b %errorlevel%
:native
"Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3\Dawnwood_GPU_v0.3\bin\windows-resident-v2\dawnwood-resident-v2.exe" %*
exit /b %errorlevel%
