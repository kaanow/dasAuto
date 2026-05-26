@echo off
title BC Family Vehicle Browser
cd /d "%~dp0"

:: --- Python ---------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org and try again.
    pause
    exit /b 1
)

:: --- Venv -----------------------------------------------------------------
:: Project-local venv keeps the system Python clean.
set VENV_DIR=.venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %VENV_DIR%...
    python -m venv "%VENV_DIR%"
)
set PY=%VENV_DIR%\Scripts\python.exe
set PIP=%VENV_DIR%\Scripts\pip.exe

:: --- Dependencies ---------------------------------------------------------
"%PY%" -c "import flask, requests, bs4, PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    "%PIP%" install -q -r requirements.txt
)

:: --- Images ---------------------------------------------------------------
set IMG_COUNT=0
for /f %%i in ('dir /s /b images\*.jpg 2^>nul ^| find /c /v ""') do set IMG_COUNT=%%i
if %IMG_COUNT% LSS 12 (
    if exist data\image_seeds.json (
        echo Downloading vehicle images ^(one-time, ~1 min^)...
        "%PY%" scrapers\fetch_images.py
    ) else (
        echo NOTE: data\image_seeds.json not present; app will run with placeholder galleries.
    )
)

:: --- Port + browser -------------------------------------------------------
if "%PORT%"=="" set PORT=5000
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:%PORT%"

echo.
echo Starting BC Family Vehicle Browser on http://localhost:%PORT%
echo Close this window to stop the server.
echo.
"%PY%" app.py
pause
