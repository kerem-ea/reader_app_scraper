@echo off
setlocal
set PATH=C:\Program Files\Python310;C:\Program Files\Python310\Scripts;%APPDATA%\Python\Python310\Scripts;%PATH%

echo.
echo ==========================================
echo  Weaver - Building Python wheel
echo ==========================================
python -m build
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Weaver - Building standalone reader.exe
echo ==========================================
cd src\weaver\app
pyinstaller --noconfirm --clean reader.spec
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