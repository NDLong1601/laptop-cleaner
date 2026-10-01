@echo off
cd /d "%~dp0"
echo ===========================================
echo   Laptop Cleaner ^& Optimizer - Launcher
echo ===========================================
echo.
echo [*] Dang khoi dong chuong trinh...
python src\main.py
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Chuong trinh gap loi (ma loi: %errorlevel%).
    echo [GI Y] Hay thu chay lai voi quyen Administrator (chuot phai -^> Run as administrator)
    pause
)
