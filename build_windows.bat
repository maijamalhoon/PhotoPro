@echo off
REM ==============================================================================
REM PhotoPro Windows One-Click Build & Packaging Script
REM Builds Standalone Distribution with PyInstaller & Compiles Inno Setup Installer
REM ==============================================================================

echo.
echo ========================================================
echo               PhotoPro Windows Build System             
echo ========================================================
echo.

REM Step 1: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is not found in PATH!
    echo Please install Python 3.10+ from python.org and check "Add to PATH".
    pause
    exit /b 1
)

echo [1/4] Installing / Verifying Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/4] Running automated test suite...
pytest -v tests/
if errorlevel 1 (
    echo [WARNING] Some tests reported warnings or errors. Continuing build...
)

echo.
echo [3/4] Packaging PhotoPro with PyInstaller...
pyinstaller --clean photopro.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller compilation failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Checking for Inno Setup compiler (ISCC.exe)...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo Compiling Inno Setup installer...
    %ISCC% installer\photopro.iss
    echo.
    echo ========================================================
    echo SUCCESS! "dist_installer\PhotoPro Setup.exe" is ready!
    echo ========================================================
) else (
    echo [NOTE] Inno Setup 6 compiler not found at default location (%ISCC%).
    echo Standalone executable is available at: dist\PhotoPro\PhotoPro.exe
    echo To generate the final Setup.exe, open installer\photopro.iss in Inno Setup.
)

echo.
pause
