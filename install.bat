@echo off
setlocal
cd /d "%~dp0"
title Jarvis Agent - Installation

echo === Jarvis Agent Installation ===
echo.

where python >nul 2>nul
if errorlevel 1 goto nopython

echo [OK] Python found.

if exist venv goto skipvenv
echo Creating virtual environment...
python -m venv venv

:skipvenv
call venv\Scripts\activate.bat

echo Installing core requirements...
python -m pip install --upgrade pip -q
pip install -r requirements-core.txt -q
if errorlevel 1 goto installfailed
echo [OK] Core requirements installed.

echo.
set /p install_gmail=Install Gmail support? [y/n]: 
if /i "%install_gmail%"=="y" pip install -r requirements-gmail.txt -q

set /p install_telegram=Install Telegram bot support? [y/n]: 
if /i "%install_telegram%"=="y" pip install -r requirements-telegram.txt -q

set /p install_office=Install Office support - Word/Excel/PowerPoint? [y/n]: 
if /i "%install_office%"=="y" pip install -r requirements-office.txt -q

set /p install_images=Install image editing support? [y/n]: 
if /i "%install_images%"=="y" pip install -r requirements-images.txt -q

set /p install_files=Install safe file-to-trash support? [y/n]: 
if /i "%install_files%"=="y" pip install -r requirements-files.txt -q

echo.
echo === Installation complete ===
echo.
echo Next steps:
echo   1. Set your Claude API key (or just run Jarvis.bat and paste it when asked)
echo   2. Run check_setup.py to verify everything
echo   3. Double-click Jarvis.bat to start
echo.
pause
exit /b 0

:nopython
echo ERROR: Python was not found. Please install Python 3.10+ first.
echo See INSTALL.md for download instructions.
pause
exit /b 1

:installfailed
echo ERROR: Failed to install core requirements. Check your internet connection.
pause
exit /b 1
