# Enhanced Face Detection System Launcher
# PowerShell script for advanced users

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Enhanced Face Detection System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Find Python executable
$pythonExe = $null
$pythonPaths = @(
    "C:\Users\baves\AppData\Local\Programs\Python\Python311\python.exe",
    "python",
    "python3"
)

foreach ($path in $pythonPaths) {
    try {
        $version = & $path --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = $path
            Write-Host "Found Python: $path ($version)" -ForegroundColor Green
            break
        }
    }
    catch {
        continue
    }
}

if (-not $pythonExe) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or ensure it's in PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Installing/Updating Dependencies" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

try {
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        throw "Package installation failed"
    }
    
    Write-Host "Dependencies updated successfully!" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to install dependencies: $_" -ForegroundColor Red
    Read-Host "Press Enter to continue anyway"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Database Setup" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

try {
    & $pythonExe manage.py makemigrations
    & $pythonExe manage.py migrate
    Write-Host "Database migrations completed!" -ForegroundColor Green
}
catch {
    Write-Host "WARNING: Database migration issues: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Starting Enhanced Detection System" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "The system will:" -ForegroundColor White
Write-Host "• Start Django web server at http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "• Open your web browser automatically" -ForegroundColor Cyan
Write-Host "• Start camera detection with live feed" -ForegroundColor Cyan
Write-Host ""

Write-Host "Controls:" -ForegroundColor White
Write-Host "• Web Interface: Use Start/Stop Camera buttons" -ForegroundColor Yellow
Write-Host "• Camera Window: Press 'q' to quit, 'r' to reload faces" -ForegroundColor Yellow
Write-Host ""

Write-Host "Starting in 3 seconds..." -ForegroundColor Magenta
Start-Sleep -Seconds 3

try {
    & $pythonExe enhanced_detector.py
}
catch {
    Write-Host "ERROR: Failed to start detection system: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "System stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"
