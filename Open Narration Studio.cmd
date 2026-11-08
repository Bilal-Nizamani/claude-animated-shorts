@echo off
setlocal
set "python=%~dp0..\shorts-runtime\tts-venv\Scripts\python.exe"
if not exist "%python%" (
    echo Run templates\voice\setup-qwen.ps1 first. See references\PRODUCTION.md.
    pause
    exit /b 1
)
"%python%" -B "%~dp0templates\voice\qwen_studio.py" %*
if errorlevel 1 pause
