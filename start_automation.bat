@echo off
REM ============================================================
REM Volunteer Management System - GitHub Pages Build Script
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Building GitHub Pages Artifacts
echo ============================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found.
    echo Create it with:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Publishing exports to docs/ for GitHub Pages...
python scripts\vms.py publish-pages --convert-first

echo.
echo Generating QR codes...
python scripts\vms.py generate-qrs

echo.
echo ============================================================
echo  Done. Commit and push so GitHub Pages updates.
echo ============================================================
echo.

pause

