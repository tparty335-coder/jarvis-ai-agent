@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title ========== JARVIS - FULL AUTO SETUP ==========
color 0B

echo.
echo  ============================================
echo  =     JARVIS AI - FULL AUTO INSTALLER      =
echo  =     v3.0 - Zero Config Setup             =
echo  ============================================
echo.

:: ============================================
:: STEP 0: Find REAL Python (not Windows Store stub)
:: ============================================
echo [STEP 0] Searching for Python...

set PYTHON_EXE=

:: Try py launcher first (most reliable on Windows)
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    :: Verify it's real python, not a stub
    py -3 -c "import sys; sys.exit(0)" >nul 2>&1
    if !errorlevel!==0 (
        set PYTHON_EXE=py -3
        echo   [OK] Found: py -3
        goto :pythonfound
    )
)

:: Try python in PATH
python --version >nul 2>&1
if %errorlevel%==0 (
    :: Check if it's the real python (not MS Store stub)
    python -c "import sys; sys.exit(0)" >nul 2>&1
    if !errorlevel!==0 (
        set PYTHON_EXE=python
        echo   [OK] Found: python
        goto :pythonfound
    )
)

:: Search common installation paths
for %%p in (
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist %%~p (
        set "PYTHON_EXE=%%~p"
        echo   [OK] Found: %%~p
        goto :pythonfound
    )
)

:: ============================================
:: STEP 0b: Python NOT found — AUTO-DOWNLOAD & INSTALL
:: ============================================
echo.
echo   [!] Python NOT found on this machine.
echo   [>>] Auto-downloading Python 3.12 — please wait...
echo.

set "PYTHON_INSTALLER=%TEMP%\python-3.12.8-amd64.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"

:: Download using curl (built into Windows 10/11)
echo   Downloading from python.org ...
curl -L -o "%PYTHON_INSTALLER%" "%PYTHON_URL%" --progress-bar
if errorlevel 1 (
    echo.
    echo   [ERROR] Download failed! Check your internet connection.
    echo   You can manually download Python from: https://python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo   [OK] Download complete.
echo.
echo   [>>] Installing Python 3.12 (this takes about 1-2 minutes)...
echo       Please wait and do NOT close this window...
echo.

:: Silent install: current user only, add to PATH, include pip
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0 Include_launcher=1
if errorlevel 1 (
    echo   [ERROR] Silent install failed. Trying interactive install...
    echo   Please check "Add Python to PATH" during installation!
    "%PYTHON_INSTALLER%"
)

:: Clean up installer
del "%PYTHON_INSTALLER%" 2>nul

echo   [OK] Python installation finished.
echo.

:: Refresh PATH for this session
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312\;%LOCALAPPDATA%\Programs\Python\Python312\Scripts\;%PATH%"

:: Try to find Python again after installation
echo   [>>] Verifying new Python installation...

:: Check the expected install location first
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    echo   [OK] Found: %PYTHON_EXE%
    goto :pythonfound
)

:: Try py launcher
py -3 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=py -3
    echo   [OK] Found: py -3
    goto :pythonfound
)

:: Try python in PATH
python -c "import sys; sys.exit(0)" >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_EXE=python
    echo   [OK] Found: python
    goto :pythonfound
)

echo.
echo   [ERROR] Python installation could not be verified.
echo   Please restart this script, or install Python manually from:
echo   https://python.org/downloads/
echo   IMPORTANT: CHECK the box "Add Python to PATH"
echo.
pause
exit /b 1

:pythonfound
echo   Using: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

:: ============================================
:: STEP 1: Create Virtual Environment
:: ============================================
echo [STEP 1] Setting up virtual environment...

if not exist "venv" (
    %PYTHON_EXE% -m venv venv
    if errorlevel 1 (
        echo   [ERROR] Failed to create venv. Trying without venv...
        goto :novenv
    )
    echo   [OK] venv created.
) else (
    echo   [OK] venv already exists.
)

call venv\Scripts\activate.bat
:: CRITICAL: After activation, use 'python' which now points to venv's python
set PYTHON_EXE=python
echo   [OK] venv activated.
goto :installpkgs

:novenv
:: If venv fails, use system Python directly
echo   [WARN] Running without venv.

:installpkgs
:: ============================================
:: STEP 2: Install ALL required packages
:: ============================================
echo.
echo [STEP 2] Installing required packages...
echo   This may take 1-3 minutes on first run...
echo.

python -m pip install --upgrade pip --quiet 2>nul

echo   Installing PyQt6...
python -m pip install PyQt6 --quiet
if errorlevel 1 (
    echo   [WARN] PyQt6 install had issues, retrying...
    python -m pip install PyQt6
)

echo   Installing Google Gemini AI (new SDK)...
python -m pip install google-genai --quiet

echo   Installing httpx...
python -m pip install httpx --quiet

echo   Installing Speech Recognition...
python -m pip install SpeechRecognition --quiet

echo   Installing Text-to-Speech...
python -m pip install pyttsx3 --quiet

echo   Installing python-dotenv...
python -m pip install python-dotenv --quiet

echo   Installing PyAudio (optional - may skip)...
python -m pip install pyaudio --quiet 2>nul

echo.
echo   [OK] All packages installed.

:: ============================================
:: STEP 3: Quick package verification
:: ============================================
echo.
echo [STEP 3] Verifying installation...

%PYTHON_EXE% -c "from PyQt6.QtWidgets import QApplication; print('   [OK] PyQt6')" 2>&1
%PYTHON_EXE% -c "import google.generativeai; print('   [OK] Google Gemini AI')" 2>&1
%PYTHON_EXE% -c "import pyttsx3; print('   [OK] pyttsx3')" 2>&1
%PYTHON_EXE% -c "import speech_recognition; print('   [OK] SpeechRecognition')" 2>&1

:: ============================================
:: STEP 4: LAUNCH JARVIS!
:: ============================================
echo.
echo ============================================
echo   ALL READY! Launching Jarvis AI Agent...
echo ============================================
echo.
echo   (If this is first run, a setup page will
echo    appear asking for your Google API Key)
echo.

%PYTHON_EXE% gui.py 2>error_launch.log

:: If we get here, the app closed
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo   [!] Jarvis exited with error code: %errorlevel%
    echo.
    if exist "error_crash.log" (
        echo   --- error_crash.log ---
        type error_crash.log
        echo.
    )
    if exist "error_launch.log" (
        echo   --- stderr output ---
        type error_launch.log
        echo.
    )
    echo ============================================
) else (
    echo   Jarvis closed normally.
)

echo.
pause
