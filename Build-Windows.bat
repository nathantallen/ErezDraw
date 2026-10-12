@echo off
setlocal
cd /d "%~dp0"
py -3.12 -c "import sys,struct; assert struct.calcsize('P')==8"
if errorlevel 1 goto python_missing
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" build_windows.py
if errorlevel 1 goto failed
echo.
echo Ready: dist\ErezDraw\ErezDraw.exe
start "" "%~dp0dist\ErezDraw"
pause
exit /b 0
:python_missing
echo Install 64-bit Python 3.12 from python.org and include the Python Launcher.
echo Then run this build script again.
pause
exit /b 1
:failed
echo Build failed. See the error above.
pause
exit /b 1
