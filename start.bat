@echo off
title DummyForge
setlocal
cd /d "%~dp0"

rem === Cek Python ===
where python >nul 2>nul
if errorlevel 1 (
    echo [GAGAL] Python tidak ditemukan di PATH.
    echo Install Python 3.10+ dari python.org, centang "Add to PATH", lalu jalankan lagi.
    pause
    exit /b 1
)

rem === Cek pip (dibutuhkan instalasi dependency) ===
python -m pip --version >nul 2>nul
if errorlevel 1 (
    echo [GAGAL] pip tidak tersedia di Python ini.
    echo Jalankan: python -m ensurepip --upgrade   lalu coba lagi.
    pause
    exit /b 1
)

rem === Cek ^& install dependency dari requirements.txt saat belum ada ===
python -c "import customtkinter" >nul 2>nul
if errorlevel 1 (
    echo First run: menginstall dependency dari requirements.txt ...
    python -m pip install -r "%~dp0requirements.txt"
    python -c "import customtkinter" >nul 2>nul
    if errorlevel 1 (
        echo [GAGAL] Install dependency tidak berhasil.
        echo Periksa koneksi internet, atau install manual: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo Dependency siap.
)

rem === Jalankan aplikasi tanpa jendela konsol (path penuh agar stop.bat bisa mencocokkan) ===
where pythonw >nul 2>nul
if errorlevel 1 (
    start "Dummy File Generator" python "%~dp0main.py"
) else (
    start "Dummy File Generator" pythonw "%~dp0main.py"
)
exit /b 0
