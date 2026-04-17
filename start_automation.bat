@echo off
REM ============================================================
REM Volunteer Management System - Automation Startup Script
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  🚀 Starting Volunteer Management Automation System
echo ============================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ ERROR: Virtual environment not found!
    echo.
    echo Please create a virtual environment first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating Python virtual environment...
call venv\Scripts\activate.bat

REM Check if AppFlowy exports exist
echo.
echo 📤 Checking AppFlowy exports...

if not exist "appflowy_exports\volunteers.json" (
    echo ⚠️  WARNING: volunteers.json not found
    echo   Please export from AppFlowy first:
    echo   1. Open AppFlowy workspace
    echo   2. Export Volunteers table to CSV
    echo   3. Save to: appflowy_exports/volunteers.csv
)

if not exist "appflowy_exports\shifts.json" (
    echo ⚠️  WARNING: shifts.json not found
    echo   Please export from AppFlowy first:
    echo   1. Open AppFlowy workspace
    echo   2. Export Shifts table to CSV
    echo   3. Save to: appflowy_exports/shifts.csv
)

if exist "appflowy_exports\volunteers.csv" (
    echo 📋 Found CSV exports, converting to JSON...
    python scripts\csv_to_json_converter.py
)

REM Run initial sync
echo.
echo 🔄 Running initial AppFlowy → Supabase sync...
python scripts\appflowy_sync_manager.py

REM Check system status
echo.
echo 🔍 Checking system status...
python scripts\check_status.py

REM Create logs directory
if not exist "logs\" mkdir logs

REM Start daemons in background windows
echo.
echo ⏳ Starting background services...
echo.

echo 📧 Starting email reminder daemon...
start "Reminder Daemon" cmd /c "python scripts\reminder_daemon.py"

echo 🔄 Starting data sync daemon...
start "Data Sync Daemon" cmd /c "python scripts\data_sync_daemon.py"

echo 📅 Syncing calendar...
python scripts\calendar_sync.py

echo 🔳 Generating QR codes for upcoming shifts...
python setup_checkin_system.py

echo 🌐 Starting web check-in server...
start "Check-in Server" cmd /c "python web\check_in_app.py"

REM Summary
echo.
echo ============================================================
echo ✅ All systems started!
echo ============================================================
echo.
echo 📍 SERVICE INFORMATION:
echo   🌐 Check-in app: http://localhost:5000
echo.
echo 📋 MONITOR LOGS:
echo   📧 Reminder daemon: logs\reminder_daemon.log
echo   🔄 Data sync: logs\data_sync_daemon.log
echo   🌐 Web app: logs\check_in_app.log
echo.
echo   View logs with:
echo   type logs\reminder_daemon.log
echo   or use: tail -f logs\reminder_daemon.log (in Git Bash)
echo.
echo 🛑 TO STOP ALL SERVICES:
echo   Run: stop_automation.bat
echo.
echo 💡 FIRST TIME USAGE:
echo   1. Set up .env file with your API keys
echo   2. Export volunteers.csv and shifts.csv from AppFlowy
echo   3. Re-run this script
echo.
echo ============================================================
echo.

pause
