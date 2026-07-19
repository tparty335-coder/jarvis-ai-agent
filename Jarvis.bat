@echo off
setlocal
cd /d "%~dp0"
title Jarvis Agent

if not exist venv goto novenv

call venv\Scripts\activate.bat

python -c "import anthropic" 2>nul
if errorlevel 1 goto missingcore

if "%ANTHROPIC_API_KEY%"=="" goto asktoken
goto run

:asktoken
echo ANTHROPIC_API_KEY is not set for this session.
set /p ANTHROPIC_API_KEY=Paste your Claude API key here: 
if "%ANTHROPIC_API_KEY%"=="" goto nokey
goto run

:run
python cli.py
echo.
echo Jarvis has stopped.
pause
exit /b 0

:novenv
echo ERROR: Virtual environment not found.
echo Please run install.bat first, then try again.
pause
exit /b 1

:missingcore
echo ERROR: Required Python packages are not installed.
echo Please run install.bat first, then try again.
pause
exit /b 1

:nokey
echo ERROR: No API key entered. Cannot start Jarvis without it.
pause
exit /b 1
