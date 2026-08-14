@echo off
setlocal

rem ---- Locate a Python 3.10+ interpreter (py launcher preferred) ----
set "PY=python"
where py >nul 2>nul
if %errorlevel% equ 0 set "PY=py -3"

%PY% --version >nul 2>nul
if errorlevel 1 (
    echo Python not found. Install Python 3.10+ and add it to PATH, then re-run.
    exit /b 1
)

rem ---- Install build tools if missing (they are not runtime deps) ----
%PY% -c "import build" >nul 2>nul
if errorlevel 1 (
    echo Installing 'build'...
    %PY% -m pip install --quiet build
    if errorlevel 1 goto :error
)

%PY% -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo Installing 'pyinstaller'...
    %PY% -m pip install --quiet pyinstaller
    if errorlevel 1 goto :error
)

echo.
echo ==========================================
echo  Weaver - Building Python wheel
echo ==========================================
%PY% -m build
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Weaver - Building standalone reader.exe
echo ==========================================
cd src\weaver\app
%PY% -m PyInstaller --noconfirm --clean reader.spec
if errorlevel 1 goto :error
cd ..\..\..

copy /Y src\weaver\app\dist\reader.exe reader.exe
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Build complete.
echo   wheel:     dist\*.whl
echo   sdist:     dist\*.tar.gz
echo   reader:    reader.exe
echo ==========================================
exit /b 0

:error
echo.
echo Build FAILED.
exit /b 1
