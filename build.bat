@echo off
cd /d "%~dp0"
echo.
echo ===========================================
echo   BUILD: Laptop Cleaner ^& Optimizer EXE
echo ===========================================
echo.

:: Xoa cache cu
echo [1/4] Don dep cache cu...
if exist dist\LaptopCleaner.exe del /f /q dist\LaptopCleaner.exe
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"

echo [2/4] Kiem tra PyInstaller...
python -m pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] PyInstaller chua duoc cai dat. Chay: pip install pyinstaller
    pause
    exit /b 1
)

echo [3/4] Bat dau build EXE (co the mat 2-5 phut)...
python -m pyinstaller laptop_cleaner.spec --clean --noconfirm

echo [4/4] Kiem tra ket qua...
if exist dist\LaptopCleaner.exe (
    echo.
    echo [OK] BUILD THANH CONG!
    echo ===========================================
    echo   File: dist\LaptopCleaner.exe
    for %%A in (dist\LaptopCleaner.exe) do echo   Kich thuoc: %%~zA bytes
    echo ===========================================
    echo.
    set /p OPEN="Mo thu muc dist? (Y/N): "
    if /i "%OPEN%"=="Y" explorer dist
) else (
    echo.
    echo [LOI] Build that bai! Xem log phia tren de tim nguyen nhan.
    pause
    exit /b 1
)

pause
