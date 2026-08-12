@echo off
set PATH=C:\Program Files\Python310;C:\Program Files\Python310\Scripts;%APPDATA%\Python\Python310\Scripts;%PATH%
cd reading_app
pyinstaller reader.spec
cd ..
copy /Y reading_app\dist\reader.exe reader.exe
