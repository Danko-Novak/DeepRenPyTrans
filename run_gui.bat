@echo off
chcp 65001 >nul
title DeepRenPyTrans Web Console
echo ============================================================
echo   🎮 Starting DeepRenPyTrans Web Console...
echo ============================================================

echo.

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please install Python and make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Run the python GUI server
python "%~dp0gui_server.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Web console server exited with an error.
    echo.
    pause
)
