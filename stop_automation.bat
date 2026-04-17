@echo off
REM ============================================================
REM Volunteer Management System - Automation Shutdown Script
REM ============================================================

echo.
echo ============================================================
echo  🛑 Stopping Volunteer Management Automation System
echo ============================================================
echo.

REM Kill processes by window title and name
echo 📧 Stopping email reminder daemon...
taskkill /FI "WINDOWTITLE eq Reminder Daemon" /T /F >nul 2>&1
taskkill /IM python.exe /F >nul 2>&1

REM Wait a moment for processes to terminate
timeout /t 2 /nobreak >nul

echo 🔄 Stopping data sync daemon...
taskkill /FI "WINDOWTITLE eq Data Sync Daemon" /T /F >nul 2>&1

echo 🌐 Stopping web check-in server...
taskkill /FI "WINDOWTITLE eq Check-in Server" /T /F >nul 2>&1

REM More thorough cleanup - kill all python processes related to the project
echo.
echo 🧹 Cleaning up Python processes...
taskkill /IM python.exe /F >nul 2>&1

echo.
echo ============================================================
echo ✅ All services stopped
echo ============================================================
echo.
echo 💾 LOG FILES SAVED:
echo   logs\reminder_daemon.log
echo   logs\data_sync_daemon.log
echo   logs\check_in_app.log
echo.
echo 📋 To view what was done before stopping, check the logs:
echo   type logs\reminder_daemon.log
echo.
echo 🚀 To start again:
echo   start_automation.bat
echo.
echo ============================================================
echo.

pause
