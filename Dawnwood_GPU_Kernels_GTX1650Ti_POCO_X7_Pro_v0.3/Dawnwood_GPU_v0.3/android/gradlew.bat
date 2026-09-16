@echo off
set DIR=%~dp0
if not exist "%DIR%gradle\wrapper\gradle-wrapper.jar" (
  python "%DIR%..\tools\bootstrap_gradle.py"
  if errorlevel 1 exit /b 1
)
java -classpath "%DIR%gradle\wrapper\gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain %*
