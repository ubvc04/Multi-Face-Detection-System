#!/usr/bin/env python
"""
Enhanced Face Detection System with Web Integration
Auto-starts with Django server and integrates with web interface

Usage: python enhanced_detector.py
"""

import cv2
import face_recognition
import numpy as np
import requests
import json
import base64
import os
import sys
import time
import logging
import threading
import signal
import subprocess
from datetime import datetime, timedelta
from queue import Queue
import webbrowser

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_security.settings')
import django
django.setup()

from faces.models import Person, FaceEncoding, SystemSettings, DetectionLog
from faces.utils import load_known_faces, compare_faces, get_system_setting, send_alert_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('face_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedFaceDetectionSystem:
    def __init__(self, auto_start_server=True, open_browser=True):
        self.camera_index = 0
        self.api_url = 'http://127.0.0.1:8000/api/detection/'
        self.server_url = 'http://127.0.0.1:8000/'
        self.cap = None
        self.known_faces = {}
        self.last_alert_time = {}
        self.running = False
        self.server_process = None
        self.auto_start_server = auto_start_server
        self.open_browser = open_browser
        
        # Configuration
        self.recognition_threshold = 0.45
        self.alert_cooldown = 300
        self.email_alerts_enabled = True
        self.multiple_face_detection = True
        
        # Performance settings
        self.frame_skip = 2
        self.frame_counter = 0
        self.resize_factor = 0.5
        
        # Detection statistics
        self.total_detections = 0
        self.unknown_detections = 0
        self.known_detections = 0
        self.last_fps_time = time.time()
        self.fps_counter = 0
        
        logger.info("Enhanced Face Detection System initialized")

    def start_django_server(self):
        """Start Django development server"""
        try:
            # Check if server is already running
            if self.is_server_running():
                logger.info("Django server is already running")
                return True
            
            logger.info("Starting Django development server...")
            
            # Try to use the correct Python executable
            python_exe = self.get_python_executable()
            
            # Start the server process
            cmd = [python_exe, 'manage.py', 'runserver', '127.0.0.1:8000']
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait a few seconds for server to start
            time.sleep(5)
            
            if self.is_server_running():
                logger.info("Django server started successfully")
                
                # Open browser if requested
                if self.open_browser:
                    try:
                        webbrowser.open(self.server_url)
                        logger.info("Opened web browser")
                    except Exception as e:
                        logger.warning(f"Could not open browser: {e}")
                
                return True
            else:
                logger.error("Failed to start Django server")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Django server: {e}")
            return False

    def get_python_executable(self):
        """Get the correct Python executable path"""
        # Try different Python paths
        possible_paths = [
            sys.executable,
            'C:/Users/baves/AppData/Local/Programs/Python/Python311/python.exe',
            'python',
            'python3'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Using Python executable: {path}")
                    return path
            except:
                continue
        
        logger.warning("Could not find Python executable, using default")
        return sys.executable

    def is_server_running(self):
        """Check if Django server is running"""
        try:
            response = requests.get(self.server_url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def initialize_camera(self):
        """Initialize camera with error handling"""
        try:
            logger.info(f"Initializing camera {self.camera_index}...")
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                # Try alternative camera indices
                for cam_idx in range(1, 5):
                    logger.info(f"Trying camera {cam_idx}...")
                    self.cap = cv2.VideoCapture(cam_idx)
                    if self.cap.isOpened():
                        self.camera_index = cam_idx
                        break
                else:
                    raise Exception("No cameras found")
            
            # Set camera properties for optimal performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test camera
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Failed to read from camera")
            
            logger.info(f"Camera {self.camera_index} initialized successfully")
            logger.info(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            self.show_camera_error_help()
            return False

    def show_camera_error_help(self):
        """Show helpful camera troubleshooting information"""
        logger.error("=" * 60)
        logger.error("CAMERA ERROR - TROUBLESHOOTING HELP")
        logger.error("=" * 60)
        logger.error("1. Check if camera is connected and not used by other apps")
        logger.error("2. Try closing Skype, Teams, or other video apps")
        logger.error("3. Check Windows Privacy Settings > Camera permissions")
        logger.error("4. Try running as administrator")
        logger.error("5. Install camera drivers if using external camera")
        logger.error("=" * 60)

    def load_known_faces_from_db(self):
        """Load known faces with error handling"""
        try:
            self.known_faces = load_known_faces()
            logger.info(f"Loaded {len(self.known_faces)} known persons from database")
            
            total_encodings = sum(len(encodings) for encodings in self.known_faces.values())
            logger.info(f"Total face encodings: {total_encodings}")
            
            if len(self.known_faces) == 0:
                logger.warning("No known faces found in database!")
                logger.warning("Register faces using the web interface at: " + self.server_url)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
            return False

    def load_system_settings(self):
        """Load system settings from database"""
        try:
            self.recognition_threshold = float(get_system_setting('recognition_threshold', '0.45'))
            self.alert_cooldown = int(get_system_setting('alert_cooldown', '300'))
            self.email_alerts_enabled = get_system_setting('email_alerts', 'True') == 'True'
            
            logger.info(f"Settings loaded - Threshold: {self.recognition_threshold}, "
                       f"Cooldown: {self.alert_cooldown}s, Email: {self.email_alerts_enabled}")
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")

    def process_frame_multiple_faces(self, frame):
        """Enhanced frame processing with improved multiple face detection and recognition"""
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=self.resize_factor, fy=self.resize_factor)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find all faces in the frame
            face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
            
            if not face_locations:
                return []
            
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            detections = []
            
            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Scale back face location to original frame size
                top, right, bottom, left = face_location
                top = int(top / self.resize_factor)
                right = int(right / self.resize_factor)
                bottom = int(bottom / self.resize_factor)
                left = int(left / self.resize_factor)
                
                scaled_location = (top, right, bottom, left)
                
                # Enhanced face recognition with distance-based matching
                best_match = None
                best_confidence = 0.0
                best_distance = float('inf')
                
                for person_name, person_encodings in self.known_faces.items():
                    try:
                        # Calculate distances to all encodings for this person
                        distances = face_recognition.face_distance(person_encodings, face_encoding)
                        min_distance = np.min(distances)
                        
                        # Convert distance to confidence (more accurate formula)
                        confidence = max(0.0, 1.0 - (min_distance / 1.0))
                        
                        # Check if this is the best match so far
                        if min_distance < best_distance and min_distance <= self.recognition_threshold:
                            # Additional confidence check
                            if confidence >= 0.5:  # Minimum confidence threshold
                                best_match = person_name
                                best_confidence = confidence
                                best_distance = min_distance
                        
                    except Exception as e:
                        logger.debug(f"Error comparing face with {person_name}: {e}")
                        continue
                
                # Create detection result
                detection = {
                    'face_location': scaled_location,
                    'person_name': best_match,
                    'confidence_score': best_confidence,
                    'distance': best_distance,
                    'is_recognized': best_match is not None,
                    'face_encoding': face_encoding,
                    'face_index': i
                }
                
                detections.append(detection)
                
                # Update statistics
                self.total_detections += 1
                if detection['is_recognized']:
                    self.known_detections += 1
                    logger.info(f"Recognized: {best_match} (confidence: {best_confidence:.3f}, distance: {best_distance:.3f})")
                else:
                    self.unknown_detections += 1
                    logger.info(f"Unknown person detected (best distance: {best_distance:.3f})")
                
                # Log detection with enhanced validation
                self.log_detection_enhanced(frame, detection)
            
            # Handle multiple faces with improved logic
            if len(detections) > 1:
                logger.info(f"Multiple faces detected: {len(detections)} faces")
                self.handle_multiple_faces_enhanced(frame, detections)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return []

    def handle_multiple_faces_enhanced(self, frame, detections):
        """Enhanced handling of multiple faces with better categorization"""
        try:
            unknown_faces = [d for d in detections if not d['is_recognized']]
            known_faces = [d for d in detections if d['is_recognized']]
            
            # Create detailed summary
            known_names = [d['person_name'] for d in known_faces]
            summary = f"Multiple faces: {len(known_faces)} known ({', '.join(known_names)}), {len(unknown_faces)} unknown"
            logger.info(summary)
            
            # Send alert only if there are unknown faces with sufficient confidence gap
            if unknown_faces:
                # Check if unknown faces are clearly unknown (not just low confidence known faces)
                clearly_unknown = []
                for unknown in unknown_faces:
                    if unknown['distance'] > (self.recognition_threshold + 0.1):  # Clear gap
                        clearly_unknown.append(unknown)
                
                if clearly_unknown:
                    self.send_multiple_faces_alert_enhanced(frame, detections, summary)
                
        except Exception as e:
            logger.error(f"Error handling multiple faces: {e}")

    def log_detection_enhanced(self, frame, detection):
        """Enhanced detection logging with better validation"""
        try:
            current_time = datetime.now()
            
            if not detection['is_recognized']:
                # Check cooldown period for unknown faces
                cooldown_key = f"unknown_{detection.get('face_index', 0)}"
                
                if cooldown_key in self.last_alert_time:
                    time_diff = current_time - self.last_alert_time[cooldown_key]
                    if time_diff.total_seconds() < self.alert_cooldown:
                        return  # Still in cooldown period
                
                # Only log if distance is clearly above threshold (not borderline)
                if detection.get('distance', 0) > (self.recognition_threshold + 0.05):
                    # Crop face image
                    top, right, bottom, left = detection['face_location']
                    face_crop = frame[top:bottom, left:right]
                    
                    if face_crop.size == 0:
                        logger.warning("Empty face crop, skipping detection")
                        return
                    
                    # Encode image to base64
                    _, buffer = cv2.imencode('.jpg', face_crop)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Prepare data for API
                    api_data = {
                        'detection_type': 'unknown',
                        'person_name': None,
                        'confidence_score': detection['confidence_score'],
                        'image_data': f"data:image/jpeg;base64,{image_base64}",
                        'notes': f"Unknown face detected (distance: {detection.get('distance', 0):.3f}) at {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    
                    # Send to Django API (async)
                    threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                    
                    # Update last alert time
                    self.last_alert_time[cooldown_key] = current_time
                    
                    logger.warning(f"Unknown face logged (distance: {detection.get('distance', 0):.3f})")
            
            else:
                # Log recognized faces occasionally with more details
                if self.fps_counter % 150 == 0:  # Every 150 frames (~5 seconds at 30fps)
                    api_data = {
                        'detection_type': 'recognized',
                        'person_name': detection['person_name'],
                        'confidence_score': detection['confidence_score'],
                        'image_data': None,
                        'notes': f"Recognized {detection['person_name']} (confidence: {detection['confidence_score']:.3f}, distance: {detection.get('distance', 0):.3f})"
                    }
                    
                    threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                
        except Exception as e:
            logger.error(f"Error logging detection: {e}")

    def send_multiple_faces_alert_enhanced(self, frame, detections, summary):
        """Enhanced alert for multiple faces"""
        try:
            # Create composite image with all faces
            composite_crop = self.create_composite_face_image_enhanced(frame, detections)
            
            if composite_crop is not None:
                # Encode image to base64
                _, buffer = cv2.imencode('.jpg', composite_crop)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Prepare detailed data for API
                unknown_count = len([d for d in detections if not d['is_recognized']])
                known_count = len([d for d in detections if d['is_recognized']])
                
                api_data = {
                    'detection_type': 'multiple',
                    'person_name': None,
                    'confidence_score': 0.0,
                    'image_data': f"data:image/jpeg;base64,{image_base64}",
                    'notes': f"Multiple faces: {known_count} known, {unknown_count} unknown at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {summary}"
                }
                
                # Send to Django API (async)
                threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                
        except Exception as e:
            logger.error(f"Error sending multiple faces alert: {e}")

    def create_composite_face_image_enhanced(self, frame, detections):
        """Enhanced composite image creation with labels"""
        try:
            face_crops = []
            for i, detection in enumerate(detections):
                top, right, bottom, left = detection['face_location']
                face_crop = frame[top:bottom, left:right]
                
                if face_crop.size > 0:
                    # Resize to standard size
                    face_crop = cv2.resize(face_crop, (120, 120))
                    
                    # Add label
                    label = detection['person_name'] if detection['is_recognized'] else "Unknown"
                    cv2.putText(face_crop, label, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    
                    face_crops.append(face_crop)
            
            if not face_crops:
                return None
            
            # Arrange faces horizontally
            composite = np.hstack(face_crops)
            return composite
            
        except Exception as e:
            logger.error(f"Error creating enhanced composite image: {e}")
            return None

    def send_multiple_faces_alert(self, frame, detections, summary):
        """Send alert for multiple faces including unknowns"""
        try:
            # Create composite image with all faces
            composite_crop = self.create_composite_face_image(frame, detections)
            
            if composite_crop is not None:
                # Encode image to base64
                _, buffer = cv2.imencode('.jpg', composite_crop)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Prepare data for API
                api_data = {
                    'detection_type': 'multiple_unknown',
                    'person_name': None,
                    'confidence_score': 0.0,
                    'image_data': f"data:image/jpeg;base64,{image_base64}",
                    'notes': f"Multiple faces detected: {summary} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
                
                # Send to Django API (async)
                threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                
        except Exception as e:
            logger.error(f"Error sending multiple faces alert: {e}")

    def create_composite_face_image(self, frame, detections):
        """Create a composite image showing all detected faces"""
        try:
            face_crops = []
            for detection in detections:
                top, right, bottom, left = detection['face_location']
                face_crop = frame[top:bottom, left:right]
                if face_crop.size > 0:
                    # Resize to standard size
                    face_crop = cv2.resize(face_crop, (100, 100))
                    face_crops.append(face_crop)
            
            if not face_crops:
                return None
            
            # Arrange faces horizontally
            composite = np.hstack(face_crops)
            return composite
            
        except Exception as e:
            logger.error(f"Error creating composite image: {e}")
            return None

    def log_detection(self, frame, detection):
        """Log detection with enhanced error handling"""
        try:
            if not detection['is_recognized']:
                # Check cooldown period
                current_time = datetime.now()
                cooldown_key = f"unknown_{detection.get('face_index', 0)}"
                
                if cooldown_key in self.last_alert_time:
                    time_diff = current_time - self.last_alert_time[cooldown_key]
                    if time_diff.total_seconds() < self.alert_cooldown:
                        return  # Still in cooldown period
                
                # Crop face image
                top, right, bottom, left = detection['face_location']
                face_crop = frame[top:bottom, left:right]
                
                if face_crop.size == 0:
                    logger.warning("Empty face crop, skipping detection")
                    return
                
                # Encode image to base64
                _, buffer = cv2.imencode('.jpg', face_crop)
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Prepare data for API
                api_data = {
                    'detection_type': 'unknown',
                    'person_name': None,
                    'confidence_score': detection['confidence_score'],
                    'image_data': f"data:image/jpeg;base64,{image_base64}",
                    'notes': f"Unknown face detected at {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                }
                
                # Send to Django API (async)
                threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                
                # Update last alert time
                self.last_alert_time[cooldown_key] = current_time
                
                logger.warning(f"Unknown face detected and logged")
            
            else:
                # Log recognized face occasionally
                if self.fps_counter % 100 == 0:  # Every 100 frames
                    api_data = {
                        'detection_type': 'recognized',
                        'person_name': detection['person_name'],
                        'confidence_score': detection['confidence_score'],
                        'image_data': None,
                        'notes': f"Recognized {detection['person_name']} with confidence {detection['confidence_score']:.3f}"
                    }
                    
                    threading.Thread(target=self.send_to_api, args=(api_data,)).start()
                
        except Exception as e:
            logger.error(f"Error logging detection: {e}")

    def send_to_api(self, data):
        """Send detection data to Django API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, json=data, timeout=10)
                
                if response.status_code == 200:
                    logger.debug("Detection logged to database successfully")
                    return True
                else:
                    logger.warning(f"API request failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending to API (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
        
        logger.error("Failed to send detection to API after all retries")
        return False

    def draw_enhanced_detections(self, frame, detections):
        """Draw enhanced detection boxes and labels"""
        for detection in detections:
            top, right, bottom, left = detection['face_location']
            
            # Choose color based on recognition status
            if detection['is_recognized']:
                color = (0, 255, 0)  # Green for recognized
                label = detection['person_name']
                confidence_text = f" ({detection['confidence_score']:.2f})"
            else:
                color = (0, 0, 255)  # Red for unknown
                label = "Unknown Person"
                confidence_text = f" ({detection['confidence_score']:.2f})"
            
            # Draw bounding box with thicker lines
            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            
            # Draw label background with better visibility
            label_size = cv2.getTextSize(label + confidence_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 1)[0]
            cv2.rectangle(frame, (left, bottom - 40), (left + label_size[0] + 10, bottom), color, cv2.FILLED)
            
            # Draw label text with better font
            cv2.putText(frame, label + confidence_text, (left + 5, bottom - 10), 
                       cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
        
        return frame

    def add_enhanced_overlay(self, frame):
        """Add enhanced system information overlay"""
        height, width = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay, timestamp, (10, height - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add system status
        status_lines = [
            f"Known Persons: {len(self.known_faces)}",
            f"Threshold: {self.recognition_threshold}",
            f"Total Detections: {self.total_detections}",
            f"Known: {self.known_detections} | Unknown: {self.unknown_detections}"
        ]
        
        for i, line in enumerate(status_lines):
            cv2.putText(overlay, line, (10, 30 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add instructions
        instructions = [
            "Controls: 'q' = Quit, 'r' = Reload faces, 's' = Reload settings",
            "Web Interface: " + self.server_url
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(overlay, instruction, (10, height - 60 + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return overlay

    def calculate_fps(self):
        """Calculate and display FPS"""
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            fps = self.fps_counter / (current_time - self.last_fps_time)
            logger.info(f"Processing FPS: {fps:.2f}")
            self.last_fps_time = current_time
            self.fps_counter = 0
        self.fps_counter += 1

    def run(self):
        """Main enhanced detection loop"""
        try:
            # Start Django server if requested
            if self.auto_start_server:
                if not self.start_django_server():
                    logger.error("Failed to start Django server")
                    return False
            
            # Initialize camera
            if not self.initialize_camera():
                return False
            
            # Load known faces and settings
            if not self.load_known_faces_from_db():
                logger.warning("Continuing with empty face database")
            
            self.load_system_settings()
            
            self.running = True
            logger.info("=" * 60)
            logger.info("ENHANCED FACE DETECTION SYSTEM STARTED")
            logger.info("=" * 60)
            logger.info(f"Web Interface: {self.server_url}")
            logger.info(f"Known persons: {len(self.known_faces)}")
            logger.info(f"Recognition threshold: {self.recognition_threshold}")
            logger.info(f"Email alerts: {'Enabled' if self.email_alerts_enabled else 'Disabled'}")
            logger.info("Controls: 'q' = Quit, 'r' = Reload faces, 's' = Reload settings")
            logger.info("=" * 60)
            
            # Main detection loop
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.error("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Skip frames for performance
                self.frame_counter += 1
                if self.frame_counter % self.frame_skip != 0:
                    cv2.imshow('Enhanced Face Detection System', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                
                # Process frame for multiple faces
                detections = self.process_frame_multiple_faces(frame)
                
                # Draw enhanced detections
                display_frame = self.draw_enhanced_detections(frame.copy(), detections)
                display_frame = self.add_enhanced_overlay(display_frame)
                
                # Show frame
                cv2.imshow('Enhanced Face Detection System', display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("Quit command received")
                    break
                elif key == ord('r'):
                    logger.info("Reloading known faces...")
                    self.load_known_faces_from_db()
                elif key == ord('s'):
                    logger.info("Reloading settings...")
                    self.load_system_settings()
                elif key == ord('w'):
                    logger.info("Opening web interface...")
                    webbrowser.open(self.server_url)
                
                # Calculate FPS
                self.calculate_fps()
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        finally:
            self.cleanup()
        
        return True

    def cleanup(self):
        """Enhanced cleanup with server shutdown"""
        logger.info("Shutting down Enhanced Face Detection System...")
        
        self.running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        
        # Optionally stop the Django server
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                logger.info("Django server stopped")
            except:
                logger.warning("Could not gracefully stop Django server")
        
        logger.info("Enhanced Face Detection System stopped")

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

def main():
    """Main function with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Face Detection and Recognition System')
    parser.add_argument('--no-server', action='store_true', 
                       help='Do not auto-start Django server')
    parser.add_argument('--no-browser', action='store_true', 
                       help='Do not auto-open web browser')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Camera index (default: 0)')
    
    args = parser.parse_args()
    
    # Create enhanced detection system
    detector = EnhancedFaceDetectionSystem(
        auto_start_server=not args.no_server,
        open_browser=not args.no_browser
    )
    detector.camera_index = args.camera
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, detector.signal_handler)
    signal.signal(signal.SIGTERM, detector.signal_handler)
    
    try:
        logger.info("Starting Enhanced Face Detection System...")
        success = detector.run()
        
        if success:
            logger.info("Enhanced Face Detection System completed successfully")
        else:
            logger.error("Enhanced Face Detection System failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Failed to start Enhanced Face Detection System: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
