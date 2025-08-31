# Enhanced Django Face Detection & Recognition Security System

![System Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Django](https://img.shields.io/badge/Django-4.2.7-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-red)

An advanced real-time face detection and recognition system with web interface, automatic camera integration, multiple face detection, email alerts, and comprehensive logging.

## 🚀 Key Features

### ✅ Enhanced Web Interface
- **Live Camera Feed**: Real-time video streaming in the web browser
- **Interactive Dashboard**: Start/Stop camera with web controls
- **Multiple Face Detection**: Simultaneous detection and recognition of multiple faces
- **Real-time Statistics**: Live FPS counter, detection counts, system status
- **Enhanced UI**: Bootstrap-based responsive design with real-time updates

### ✅ Advanced Detection System
- **Automatic Startup**: Django server and camera detection start together
- **Multiple Face Handling**: Detects and processes multiple faces simultaneously
- **Smart Recognition**: Confidence-based matching with adjustable thresholds
- **Error Handling**: Comprehensive error handling for camera, network, and processing issues
- **Performance Optimized**: Frame skipping, resizing, and efficient processing

### ✅ Smart Alerts & Logging
- **Email Notifications**: Automatic email alerts for unknown faces
- **Cooldown Protection**: Prevents spam alerts with configurable cooldown periods
- **Database Logging**: All detections logged with timestamps and images
- **Visual Feedback**: Real-time face bounding boxes with names and confidence scores
- **Composite Images**: Multiple face snapshots in single alert

### ✅ User Management
- **Face Registration**: Upload multiple images per person
- **Admin Dashboard**: Comprehensive management interface
- **Detection Logs**: Searchable and filterable detection history
- **System Settings**: Configurable recognition thresholds and alert settings

## 📋 Requirements

- **Python 3.11**
- **Windows 10/11** (tested)
- **Webcam** (built-in or USB)
- **Gmail account** with app password for alerts

## 🛠️ Installation & Setup

### Quick Start (Recommended)

1. **Download & Extract** the project to your desired location
2. **Double-click** `start_enhanced_system.bat` 
3. **Wait** for automatic setup and system startup
4. **Login** to web interface when browser opens (admin/admin123)

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations  
python manage.py makemigrations
python manage.py migrate

# Create admin user (if not exists)
python manage.py createsuperuser

# Start enhanced system
python enhanced_detector.py
```

## 🎯 How It Works

### Motto Implementation
**"When I run the project, it opens a web interface, camera auto-starts scanning faces in real-time, matches with database, shows names for known faces, shows Unknown for unmatched faces, saves snapshots, logs everything, and sends email alerts."**

### System Flow
1. **Auto-Start**: `enhanced_detector.py` starts Django server + camera detection
2. **Web Interface**: Browser opens to http://127.0.0.1:8000/
3. **Live Detection**: Camera feed displays in web browser with real-time face detection
4. **Recognition**: Multiple faces processed simultaneously against database
5. **Smart Logging**: Known faces logged periodically, unknown faces logged immediately
6. **Email Alerts**: Unknown faces trigger email with snapshot to baveshchowdary1@gmail.com
7. **Web Controls**: Start/Stop camera, reload faces, view logs through web interface

## 🖥️ System Components

### Enhanced Detector (`enhanced_detector.py`)
- **Auto-Server Startup**: Starts Django server automatically
- **Multi-Camera Support**: Tries multiple camera indices if primary fails
- **Multiple Face Detection**: Processes all faces in frame simultaneously
- **Smart Performance**: Adaptive frame processing for smooth operation
- **Error Recovery**: Automatic retry logic and graceful error handling

### Web Interface Features
- **Live Camera Feed**: HTTP streaming with real-time face detection overlay
- **Interactive Controls**: Start/Stop camera, reload faces, system status
- **Real-time Statistics**: FPS counter, detection counts, known faces count
- **Enhanced Dashboard**: Modern Bootstrap UI with live updates
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

### Advanced Detection Logic
- **Multiple Face Processing**: Handles 1-10+ faces simultaneously 
- **Confidence Scoring**: Adjustable recognition thresholds
- **Composite Alerts**: Multiple unknown faces in single email alert
- **Performance Optimization**: Frame skipping, resizing, threading
- **Memory Management**: Efficient face encoding comparison

## 📧 Email Configuration

**Gmail SMTP Settings** (Already Configured):
- **Email**: baveshchowdary1@gmail.com
- **App Password**: ilsp zgmj pfhj iyli
- **SMTP Server**: smtp.gmail.com:587

**Email Alert Features**:
- Unknown face snapshots
- Multiple face detection alerts
- System status notifications
- Configurable cooldown periods

## 🎮 Usage Instructions

### Starting the System

**Option 1: Auto-Start (Recommended)**
```bash
# Windows Batch File
start_enhanced_system.bat

# PowerShell (Advanced)
.\start_enhanced_system.ps1
```

**Option 2: Manual Start**
```bash
# Enhanced system with auto-server startup
python enhanced_detector.py

# Start only detection (server must be running separately)
python enhanced_detector.py --no-server

# Start without auto-opening browser
python enhanced_detector.py --no-browser
```

### Web Interface Controls

1. **Login**: http://127.0.0.1:8000/ (admin/admin123)
2. **Dashboard**: Live camera feed with Start/Stop controls
3. **Register Faces**: Upload multiple images per person
4. **View Logs**: Detection history with search and filters
5. **Settings**: Adjust recognition thresholds and email alerts

### Camera Window Controls
- **q**: Quit system
- **r**: Reload faces from database
- **s**: Reload system settings
- **w**: Open web interface

### Face Registration Process
1. Navigate to **Register Face** in web interface
2. Enter person's name
3. Upload 2-5 clear face images (different angles recommended)
4. System extracts face encodings automatically
5. Person immediately available for recognition

## 🔧 Configuration

### System Settings (Web Interface)
- **Recognition Threshold**: 0.6 (lower = more strict)
- **Email Alerts**: Enable/Disable notifications
- **Alert Cooldown**: 300 seconds between alerts
- **Camera Index**: Primary camera selection

### Performance Tuning
```python
# In enhanced_detector.py
frame_skip = 2          # Process every 2nd frame
resize_factor = 0.5     # Resize to 50% for speed
recognition_threshold = 0.6  # Confidence threshold
alert_cooldown = 300    # Seconds between alerts
```

## 🔍 Troubleshooting

### Camera Issues
```
ERROR: Camera initialization failed
SOLUTIONS:
1. Close Skype, Teams, or other video apps
2. Check Windows Privacy Settings > Camera permissions  
3. Try different camera index: python enhanced_detector.py --camera 1
4. Run as administrator
5. Install camera drivers for external cameras
```

### Module Import Errors
```
ERROR: ModuleNotFoundError: No module named 'django'
SOLUTION: Use full Python path:
C:\Users\baves\AppData\Local\Programs\Python\Python311\python.exe enhanced_detector.py
```

### Email Not Sending
```
ERROR: Email sending failures
SOLUTIONS:
1. Check internet connection
2. Verify Gmail app password: ilsp zgmj pfhj iyli
3. Check Django logs for SMTP errors
4. Temporarily disable email in settings
```

### Multiple Face Overlapping
```
ISSUE: Multiple faces too close together
SOLUTIONS:
1. Ensure good lighting and spacing
2. Adjust recognition threshold in settings
3. Use higher resolution camera
4. Position camera for optimal face view
```

### Performance Issues
```
ISSUE: Low FPS or lag
SOLUTIONS:
1. Increase frame_skip value (process fewer frames)
2. Reduce resize_factor (smaller processing size)
3. Close other applications
4. Use lower camera resolution
```

## 📁 Project Structure

```
Multi Face Detection System/
├── enhanced_detector.py          # Main enhanced detection script
├── detector.py                   # Original detection script
├── manage.py                     # Django management
├── db.sqlite3                    # Database
├── requirements.txt              # Dependencies
├── start_enhanced_system.bat     # Auto-start batch file
├── start_enhanced_system.ps1     # PowerShell launcher
├── face_security/                # Django project
│   ├── settings.py              # Enhanced settings with CORS
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # WSGI application
│   └── asgi.py                  # ASGI application
├── faces/                        # Django app
│   ├── models.py                # Database models
│   ├── views.py                 # Enhanced views with camera streaming
│   ├── urls.py                  # App URLs with camera endpoints
│   ├── utils.py                 # Face processing utilities
│   ├── consumers.py             # WebSocket consumers (future)
│   ├── routing.py               # WebSocket routing (future)
│   ├── admin.py                 # Admin interface
│   └── templates/               # Enhanced templates
│       └── faces/
│           ├── base.html        # Base template
│           ├── dashboard.html   # Enhanced dashboard with live feed
│           ├── login.html       # Login page
│           ├── register_face.html # Face registration
│           ├── person_list.html # Person management
│           ├── person_detail.html # Person details
│           ├── detection_logs.html # Detection logs
│           └── system_settings.html # Settings
├── media/                        # Uploaded images and snapshots
├── static/                       # Static files (CSS, JS)
└── logs/                         # System logs
```

## 🔐 Security Features

- **CSRF Protection**: All forms protected against cross-site attacks
- **User Authentication**: Login required for all system access
- **Input Validation**: File upload validation and sanitization
- **SQL Injection Protection**: Django ORM prevents SQL injection
- **Session Security**: Secure session management
- **CORS Configuration**: Controlled cross-origin requests

## 🚀 Advanced Features

### Real-time Web Streaming
- HTTP streaming endpoint for live camera feed
- Real-time detection overlay with bounding boxes
- FPS counter and system statistics
- Responsive video display

### Multiple Face Detection
- Simultaneous processing of multiple faces
- Individual confidence scoring per face
- Composite image alerts for multiple unknowns
- Smart cooldown per face location

### Enhanced Error Handling
- Camera fallback to alternative indices
- Network retry logic for API calls
- Graceful degradation on component failures
- Comprehensive logging and debugging

### Performance Optimization
- Adaptive frame processing
- Memory-efficient face encoding
- Threaded API communication
- Smart resource management

## 🏁 Quick Test

1. **Start System**: Double-click `start_enhanced_system.bat`
2. **Wait for Startup**: Browser opens automatically to login page
3. **Login**: admin/admin123
4. **Click "Start Camera"**: Live feed appears in dashboard
5. **Test Recognition**: Show your face to camera
6. **Register Face**: Use "Register New Face" if unknown
7. **Check Logs**: View detection history in "Detection Logs"

## 🤝 Support & Updates

### Current Version Features
- ✅ Auto-start Django server + camera
- ✅ Live web camera feed
- ✅ Multiple face detection  
- ✅ Real-time web controls
- ✅ Enhanced error handling
- ✅ Email alerts with snapshots
- ✅ Comprehensive logging
- ✅ Mobile-responsive interface

### Future Enhancements (Available on Request)
- 🔄 WebSocket real-time updates
- 📱 Mobile app integration
- 🔐 Advanced security features
- 📊 Analytics dashboard
- 🌐 Remote access capabilities
- 💾 Cloud storage integration

---

**🎯 Mission Accomplished**: Complete face detection system with web interface, automatic camera startup, multiple face detection, email alerts, and comprehensive real-time monitoring!
