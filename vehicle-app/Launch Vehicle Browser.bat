@echo off
title BC Family Vehicle Browser
cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
python -c "import flask, requests, bs4, PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt -q
    echo.
)

:: Warn if images not yet downloaded
for /f %%i in ('dir /s /b images\*.jpg 2^>nul ^| find /c /v ""') do set IMG_COUNT=%%i
if %IMG_COUNT% LSS 12 (
    echo NOTE: Only %IMG_COUNT% vehicle images found.
    echo Run this once for full image galleries:
    echo   python scrapers\fetch_images.py
    echo.
)

:: Open browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

echo Starting BC Family Vehicle Browser...
echo   http://localhost:5000
echo   Close this window to stop the server.
echo.
python app.py
pause
