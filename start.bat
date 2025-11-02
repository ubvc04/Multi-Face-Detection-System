@echo off
echo Starting Multi-Face Detection System...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Please create one first.
    echo Run: python -m venv venv
    echo.
)

REM Run Django development server
python manage.py runserver

pause
