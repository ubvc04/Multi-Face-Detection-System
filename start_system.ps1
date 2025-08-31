# Face Detection System Startup Script (PowerShell)
# This script starts both the Django server and face detection system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Face Detection Security System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please ensure venv folder exists in current directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting Django server..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:8000/" -ForegroundColor Yellow
Write-Host ""

# Start Django server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\venv\Scripts\Activate.ps1'; python manage.py runserver"

# Wait for server to start
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Django server started! You can now:" -ForegroundColor Green
Write-Host "1. Open http://127.0.0.1:8000/ in your browser" -ForegroundColor White
Write-Host "2. Login with your admin credentials" -ForegroundColor White
Write-Host "3. Register faces in the system" -ForegroundColor White
Write-Host ""
Write-Host "To start face detection, press any key..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "Starting face detection system..." -ForegroundColor Green
Write-Host "Press 'q' in the detection window to quit" -ForegroundColor Yellow
Write-Host "Press 'r' to reload faces, 's' to reload settings" -ForegroundColor Yellow
Write-Host ""

# Start face detection
python detector.py

Write-Host ""
Write-Host "Face detection stopped." -ForegroundColor Yellow
Write-Host "To stop the Django server, close the Django Server window." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
