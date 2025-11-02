Write-Host "Starting Multi-Face Detection System..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: Virtual environment not found. Please create one first." -ForegroundColor Yellow
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    Write-Host ""
}

# Run Django development server
python manage.py runserver

Read-Host -Prompt "Press Enter to exit"
