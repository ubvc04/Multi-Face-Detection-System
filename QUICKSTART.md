# 🔹 QUICK START GUIDE - Face Detection System

## Admin Credentials
- **Username:** `admin`
- **Email:** `baveshchowdary1@gmail.com`
- **Password:** `admin123`

## Important: Python Environment Issue Fix

The virtual environment activation isn't working properly with PowerShell. Here are the solutions:

### Option 1: Use Full Python Path (Recommended)
Instead of just `python`, use the full path:
```powershell
C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe manage.py runserver
C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe detector.py
```

### Option 2: Fix Virtual Environment
1. Deactivate current environment:
   ```powershell
   deactivate
   ```

2. Recreate virtual environment:
   ```powershell
   python -m venv venv --clear
   ```

3. Activate properly:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. Reinstall packages:
   ```powershell
   pip install -r requirements.txt
   ```

## Quick Start Commands

### 1. Start Django Server
```powershell
C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe manage.py runserver
```

### 2. Access Web Interface
- Open: http://127.0.0.1:8000/
- Login with admin credentials above

### 3. Start Face Detection (in new terminal)
```powershell
C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe detector.py
```

## System Status: ✅ READY
- Django server: Running on http://127.0.0.1:8000/
- Database: Configured and migrated
- Admin user: Created
- All packages: Installed
- Face detection script: Ready

## Next Steps:
1. Login to the web interface
2. Register some faces
3. Start the camera detection system
4. Monitor detections and logs

## Troubleshooting:
If you get "Module not found" errors, always use the full Python path:
`C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe`
