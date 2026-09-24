@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto resident
if /I "%~1"=="inspect" goto resident
set "DW_ENZYME_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_ENZYME_PYTHON%" goto python
set "DW_ENZYME_PYTHON=python"
:python
if /I "%~1"=="results" goto results
"%DW_ENZYME_PYTHON%" -X utf8 -B local_lab\source_enzyme.py %*
exit /b %errorlevel%
:results
"%DW_ENZYME_PYTHON%" -X utf8 -B local_lab\source_enzyme_results.py %*
exit /b %errorlevel%
:resident
call Dawnwood-Resident2.cmd %*
exit /b %errorlevel%
