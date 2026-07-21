@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Jarvis Agent - Installation
echo.
echo ============================================
echo   Jarvis AI Agent - Full Setup
echo ============================================
echo.

:: ============================================
:: Find or Auto-Install Python
:: ============================================
set PYTHON_EXE=

:: Try py launcher
py -3 -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=py -3
    goto :havepython
)

:: Try python in PATH
python -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=python
    goto :havepython
)

:: Search common paths
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%~p (
        set "PYTHON_EXE=%%~p"
        goto :havepython
    )
)

:: Auto-download Python
echo   [!] Python not found. Auto-downloading Python 3.12...
set "PYTHON_INSTALLER=%TEMP%\python-3.12.8-amd64.exe"
curl -L -o "%PYTHON_INSTALLER%" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe" --progress-bar
if errorlevel 1 (
    echo   [ERROR] Download failed. Install Python manually from https://python.org
    pause
    exit /b 1
)
echo   Installing Python 3.12 silently...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1
del "%PYTHON_INSTALLER%" 2>nul
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
    echo   [ERROR] Python install failed. Please install manually.
    pause
    exit /b 1
)

:havepython
echo [OK] Python found: %PYTHON_EXE%
%PYTHON_EXE% --version

:: Create venv if missing
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv venv
    if errorlevel 1 goto venvfail
    echo [OK] venv created.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Upgrade pip silently
python -m pip install --upgrade pip -q

:: Install everything needed for GUI + Gemini
echo.
echo Installing core packages (PyQt6, Gemini, SpeechRecognition, pyttsx3)...
pip install PyQt6 google-generativeai SpeechRecognition pyttsx3 python-dotenv -q
if errorlevel 1 goto installfailed
echo [OK] Core packages installed.

:: Install PyAudio separately (may fail on some machines - that's OK)
pip install pyaudio -q 2>nul
echo [OK] Audio support installed (or skipped if not available).

:: Optional packages
echo.
set /p install_office=Install Office support (Word/Excel/PowerPoint)? [y/n]: 
if /i "%install_office%"=="y" pip install python-docx openpyxl python-pptx -q

set /p install_files=Install safe file operations? [y/n]: 
if /i "%install_files%"=="y" pip install send2trash -q

echo.
echo ============================================
echo   Installation Complete!
echo   Now run: SETUP_AND_RUN.bat
echo ============================================
echo.
pause
exit /b 0

:venvfail
echo ERROR: Failed to create virtual environment.
pause
exit /b 1

:installfailed
echo ERROR: Failed to install packages. Check internet connection.
pause
exit /b 1
