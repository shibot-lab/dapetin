@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title DAPETIN - Local Dashboard
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "URL=http://127.0.0.1:8000/"

if not exist "%PYTHON%" (
    echo [DAPETIN] Virtual environment belum tersedia. Membuat .venv...
    py -3 -m venv "%ROOT%.venv"
    if errorlevel 1 goto :error
)

echo [DAPETIN] Memastikan package terpasang...
"%PYTHON%" -m pip install -e "%ROOT%"
if errorlevel 1 goto :error

echo [DAPETIN] Starting dashboard server...
start "DAPETIN Server" "%ComSpec%" /k "cd /d "%ROOT%" && "%PYTHON%" -m dapetin.cli dashboard --db "%ROOT%dapetin.db" --host 127.0.0.1 --port 8000"

echo [DAPETIN] Waiting for dashboard...
for /l %%N in (1,1,30) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($c) { exit 0 } else { exit 1 }" >nul 2>&1
    if not errorlevel 1 goto :open_browser
    timeout /t 1 /nobreak >nul
)

echo.
echo [DAPETIN] Dashboard gagal membuka port 8000.
echo [DAPETIN] Periksa window "DAPETIN Server" untuk error.
pause
exit /b 1

:open_browser
echo [DAPETIN] Dashboard ready. Opening browser...
start "" "%URL%"
echo [DAPETIN] DAPETIN berjalan di %URL%
exit /b 0

:error
echo.
echo [DAPETIN] Gagal menyiapkan DAPETIN.
pause
exit /b 1
