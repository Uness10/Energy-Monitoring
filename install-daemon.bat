@echo off
REM Energy Monitoring Daemon - Installation Script (Windows)
REM Run this on any Windows device to set up the daemon
REM Usage: install-daemon.bat <BACKEND_URL> <NODE_ID> [NODE_TYPE]

setlocal enabledelayedexpansion

if "%1"=="" (
    echo Usage: install-daemon.bat ^<BACKEND_URL^> ^<NODE_ID^> [NODE_TYPE]
    echo.
    echo Examples:
    echo   install-daemon.bat http://192.168.1.100:8000 workstation-01 workstation
    echo   install-daemon.bat http://192.168.1.100:8000 windows-vm windows
    exit /b 1
)

set BACKEND_URL=%1
set NODE_ID=%2
set NODE_TYPE=%3
if "%NODE_TYPE%"=="" set NODE_TYPE=windows

echo ========================================
echo Energy Monitoring Daemon - Setup
echo ========================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo.

echo Creating daemon directory...
set DAEMON_DIR=%USERPROFILE%\energy-daemon
if not exist "%DAEMON_DIR%" mkdir "%DAEMON_DIR%"
cd /d "%DAEMON_DIR%"
echo [OK] Daemon directory: %DAEMON_DIR%
echo.

echo Downloading daemon files...
if not exist "collectors" mkdir collectors

echo   Downloading daemon.py...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/daemon/daemon.py', '%DAEMON_DIR%\daemon.py')" >nul 2>&1
if errorlevel 1 echo   [WARNING] Could not download daemon.py - you may need to copy files manually

echo   Downloading buffer.py...
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/daemon/buffer.py', '%DAEMON_DIR%\buffer.py')" >nul 2>&1

echo   Downloading collectors...
for %%f in (cpu memory power temperature uptime app_energy __init__) do (
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://raw.githubusercontent.com/your-repo/Energy-Monitoring/main/daemon/collectors/%%f.py', '%DAEMON_DIR%\collectors\%%f.py')" >nul 2>&1
)
echo [OK] Daemon files ready
echo.

echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
(
    echo httpx==0.25.0
    echo pyyaml==6.0
    echo psutil==5.9.6
) > requirements.txt

pip install -q -r requirements.txt
echo [OK] Dependencies installed
echo.

echo Creating config.yaml...
(
    echo # Energy Monitoring Daemon Config
    echo # Auto-generated - %date% %time%
    echo.
    echo node_id: "%NODE_ID%"
    echo node_type: "%NODE_TYPE%"
    echo backend_url: "%BACKEND_URL%"
    echo collection_interval_seconds: 10
    echo retry_interval_seconds: 30
    echo buffer_max_records: 3600
    echo.
    echo app_tracking:
    echo   enabled: true
    echo   mode: "top_n"
    echo   top_n: 10
    echo   min_cpu_percent: 1.0
) > config.yaml
echo [OK] Configuration created
echo.

echo Creating startup scripts...

REM Create run.bat
(
    echo @echo off
    echo cd /d "%DAEMON_DIR%"
    echo call venv\Scripts\activate.bat
    echo python daemon.py
    echo pause
) > run.bat

echo [OK] Startup scripts created
echo.

echo ========================================
echo [OK] Installation Complete!
echo ========================================
echo.
echo Configuration:
echo   Backend URL: %BACKEND_URL%
echo   Node ID: %NODE_ID%
echo   Node Type: %NODE_TYPE%
echo   Directory: %DAEMON_DIR%
echo.
echo Quick Start:
echo   1. Test the daemon:
echo      %DAEMON_DIR%\run.bat
echo.
echo   2. Create a scheduled task to run at startup (optional):
echo      Open Task Scheduler and create a new task:
echo      - Trigger: At startup
echo      - Action: Start a program
echo      - Program: %DAEMON_DIR%\run.bat
echo.
echo The daemon will auto-register with the backend!
echo.
pause
