@echo off
rem voiceger-editor-ui first-time setup for Windows
setlocal
chcp 65001 >nul
set "UI_DIR=%~dp0"

if not defined VOICEGER_ROOT (
  if exist "%UI_DIR%..\voiceger_v2\" (
    set "VOICEGER_ROOT=%UI_DIR%..\voiceger_v2"
  ) else (
    set "VOICEGER_ROOT=%USERPROFILE%\voiceger_v2"
  )
)

set "PY=%VOICEGER_ROOT%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Voiceger Python not found: "%PY%"
  echo Install Voiceger first, or set VOICEGER_ROOT to your voiceger_v2 folder.
  pause
  exit /b 1
)

set PYTHONIOENCODING=utf-8
cd /d "%UI_DIR%"
"%PY%" "%UI_DIR%setup.py"
echo.
pause
endlocal
