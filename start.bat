@echo off
setlocal
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" goto missing_venv

start "Aihelper Server" /min "%PY%" -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false --server.headless true
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\wait_for_server.ps1" -Port 8501
if errorlevel 1 goto start_failed

start "" "http://localhost:8501"
exit /b 0

:missing_venv
echo Aihelper virtual environment is missing.
echo Create .venv with Python 3.12 and install requirements.txt.
pause
exit /b 1

:start_failed
echo Aihelper server did not start successfully.
pause
exit /b 1
