@echo off
set PATH=C:\Users\lost~1\AppData\Local\Programs\Python\Python314\Scripts;%PATH%
cd reading_app
pyinstaller reader_app.spec
cd ..
copy reading_app\dist\ReaderApp.exe ReaderApp.exe
