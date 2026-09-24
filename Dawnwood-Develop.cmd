@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto native
set "DW_DEVELOP_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%DW_DEVELOP_PYTHON%" set "DW_DEVELOP_PYTHON=python"
if /I "%~1"=="results" goto results
if /I "%~1"=="inspect" goto inspect
if /I "%~1"=="prepare" goto prepare
"%DW_DEVELOP_PYTHON%" -X utf8 -B -m local_lab.source_development %*
exit /b %errorlevel%
:native
"Dawnwood_GPU_Kernels_GTX1650Ti_POCO_X7_Pro_v0.3\Dawnwood_GPU_v0.3\bin\windows-resident-v3\dawnwood-resident-v3.exe" %*
exit /b %errorlevel%
:results
"%DW_DEVELOP_PYTHON%" -X utf8 -B -m local_lab.source_development_results %*
exit /b %errorlevel%
:inspect
"%DW_DEVELOP_PYTHON%" -X utf8 -B -m local_lab.source_resident_v3 %*
exit /b %errorlevel%
:prepare
"%DW_DEVELOP_PYTHON%" -X utf8 -B -m local_lab.source_development_queries %*
exit /b %errorlevel%
