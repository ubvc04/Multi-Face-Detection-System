@echo off
REM Face Detection System Startup Script
REM This script starts both the Django server and face detection system

echo ========================================
echo  Face Detection Security System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please ensure venv folder exists in current directory.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Django server...
echo Server will be available at: http://127.0.0.1:8000/
echo.

REM Start Django server in background
start "Django Server" cmd /k "python manage.py runserver"

REM Wait a moment for server to start
timeout /t 5 /nobreak >nul

echo.
echo Django server started! You can now:
echo 1. Open http://127.0.0.1:8000/ in your browser
echo 2. Login with your admin credentials
echo 3. Register faces in the system
echo.
echo To start face detection, press any key...
pause >nul

echo.
echo Starting face detection system...
echo Press 'q' in the detection window to quit
echo Press 'r' to reload faces, 's' to reload settings
echo.

REM Start face detection
python detector.py

echo.
echo Face detection stopped.
echo To stop the Django server, close the Django Server window.
echo.
pause
