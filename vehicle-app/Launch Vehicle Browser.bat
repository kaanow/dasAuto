@echo off
title Family Vehicle Browser
cd /d "%~dp0"
set SKILL_DIR=%CD%

:: --- Data directory -------------------------------------------------------
:: Default to user-kaan-and-tess beside vehicle-app\. Set VEHICLE_DATA_DIR to
:: re-point at a different per-family folder.
if "%VEHICLE_DATA_DIR%"=="" (
    pushd ..
    set VEHICLE_DATA_DIR=%CD%\user-kaan-and-tess
    popd
)
if not exist "%VEHICLE_DATA_DIR%" (
    echo ERROR: VEHICLE_DATA_DIR=%VEHICLE_DATA_DIR% does not exist.
    pause
    exit /b 1
)
if not exist "%VEHICLE_DATA_DIR%\vehicles.json" (
    echo ERROR: %VEHICLE_DATA_DIR%\vehicles.json missing - can't load candidate list.
    pause
    exit /b 1
)

:: --- Python ---------------------------------------------------------------
:: Prefer the Python launcher with an explicit 3.11+ minimum.
set PYBIN=python
where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 --version >nul 2>&1 && set PYBIN=py -3.11
)
%PYBIN% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org and try again.
    pause
    exit /b 1
)

:: --- Venv -----------------------------------------------------------------
set VENV_DIR=.venv
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment in %SKILL_DIR%\%VENV_DIR%...
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
for /f %%i in ('dir /s /b "%VEHICLE_DATA_DIR%\images\*.jpg" 2^>nul ^| find /c /v ""') do set IMG_COUNT=%%i
if %IMG_COUNT% LSS 12 (
    if exist "%VEHICLE_DATA_DIR%\image_seeds.json" (
        echo Downloading vehicle images ^(one-time, ~1 min^)...
        "%PY%" scrapers\fetch_images.py
    ) else (
        echo NOTE: %VEHICLE_DATA_DIR%\image_seeds.json not present; app will run with placeholder galleries.
    )
)

:: --- Port + browser -------------------------------------------------------
if "%PORT%"=="" set PORT=5000
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:%PORT%"

echo.
echo Starting Family Vehicle Browser on http://localhost:%PORT%
echo Data: %VEHICLE_DATA_DIR%
echo Close this window to stop the server.
echo.
"%PY%" app.py
pause
