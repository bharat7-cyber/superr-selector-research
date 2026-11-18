@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python from https://www.python.org/downloads/ and select Add Python to PATH.
  pause
  exit /b 1
)
echo Starting SupeRR Pressure Performance Lab...
echo Keep this black window open while using the website.
echo To stop the website, press CTRL+C in this window.
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"
python -m http.server 8000 --directory app
pause
