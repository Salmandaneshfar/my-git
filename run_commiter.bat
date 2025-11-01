@echo off
REM Automated Git Commiter Runner for Windows
REM This batch file can be scheduled with Windows Task Scheduler

cd /d "%~dp0"
python commiter.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred! Exit code: %ERRORLEVEL%
    pause
)

