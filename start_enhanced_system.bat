@echo off
echo ========================================
echo  Enhanced Face Detection System
echo ========================================
echo.
echo Starting system with web interface and camera detection...
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Try to find Python executable
set PYTHON_EXE=
if exist "C:\Users\baves\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE=C:\Users\baves\AppData\Local\Programs\Python\Python311\python.exe
    echo Using Python from: %PYTHON_EXE%
) else (
    set PYTHON_EXE=python
    echo Using system Python
)

echo.
echo ========================================
echo  Installing/Updating Dependencies
echo ========================================
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install -r requirements.txt

echo.
echo ========================================
echo  Running Database Migrations
echo ========================================
%PYTHON_EXE% manage.py makemigrations
%PYTHON_EXE% manage.py migrate

echo.
echo ========================================
echo  Starting Enhanced Detection System
echo ========================================
echo.
echo The system will:
echo - Start Django web server at http://127.0.0.1:8000/
echo - Open your web browser automatically
echo - Start camera detection with live feed
echo.
echo Controls:
echo - Web Interface: Use Start/Stop Camera buttons
echo - Camera Window: Press 'q' to quit, 'r' to reload faces, 's' to reload settings
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start the enhanced detector
%PYTHON_EXE% enhanced_detector.py

echo.
echo System stopped. Press any key to exit...
pause >nul
