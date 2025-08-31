@echo off
echo ========================================
echo  Face Detection System - Quick Start
echo ========================================
echo.

echo Starting Django Server...
echo Server will be available at: http://127.0.0.1:8000/
echo.
echo Admin Credentials:
echo Username: admin
echo Password: admin123
echo.

start "Django Server" cmd /k "C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe manage.py runserver"

echo Django server started in new window!
echo.
echo To start face detection, run:
echo C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe detector.py
echo.
pause
