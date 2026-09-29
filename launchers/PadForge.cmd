@echo off
rem PadForge for Windows. Double-click to start; Python is included.
cd /d "%~dp0"
"%~dp0python\python.exe" -m padforge %*
echo.
pause
