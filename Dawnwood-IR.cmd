@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto native
set "DW_IR_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_IR_PYTHON%" goto python
set "DW_IR_PYTHON=python"
:python
"%DW_IR_PYTHON%" -X utf8 -B local_lab\source_ir.py %*
exit /b %errorlevel%
:native
"Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3\Dawnwood_GPU_v0.3\bin\windows-source\dawnwood-source-ir.exe" %*
exit /b %errorlevel%
