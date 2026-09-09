@echo off
setlocal
cd /d "%~dp0"

title DAPETIN - Local Dashboard

if not exist ".venv\Scripts\python.exe" (
    echo [DAPETIN] Virtual environment belum tersedia.
    echo [DAPETIN] Membuat .venv...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo.
        echo Gagal membuat virtual environment. Pastikan Python 3.13.14 terpasang.
        pause
        exit /b 1
    )
)

echo [DAPETIN] Menyiapkan environment...
.venv\Scripts\python.exe -m pip install -e .
if errorlevel 1 (
    echo.
    echo Gagal menyiapkan DAPETIN.
    pause
    exit /b 1
)

echo.
echo [DAPETIN] Menjalankan Dashboard...
echo [DAPETIN] Buka http://127.0.0.1:8000 di browser jika belum terbuka.
echo.
.venv\Scripts\python.exe -m dapetin.cli dashboard --db dapetin.db

pause
endlocal
