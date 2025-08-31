#!/usr/bin/env python
"""
Face Detection and Recognition System
Real-time face detection script with Django integration

Usage: python detector.py
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
from datetime import datetime, timedelta
import threading
from queue import Queue
import argparse

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_security.settings')
import django
django.setup()

from faces.models import Person, FaceEncoding, SystemSettings
from faces.utils import load_known_faces, compare_faces, get_system_setting

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

class FaceDetectionSystem:
    def __init__(self, camera_index=0, api_url='http://127.0.0.1:8000/api/detection/'):
        self.camera_index = camera_index
        self.api_url = api_url
        self.cap = None
        self.known_faces = {}
        self.last_alert_time = {}
        self.detection_queue = Queue()
        self.running = False
        
        # Configuration
        self.recognition_threshold = float(get_system_setting('recognition_threshold', '0.6'))
        self.alert_cooldown = int(get_system_setting('alert_cooldown', '300'))
        self.email_alerts_enabled = get_system_setting('email_alerts', 'True') == 'True'
        
        # Performance settings
        self.frame_skip = 2  # Process every 2nd frame for better performance
        self.frame_counter = 0
        self.resize_factor = 0.5  # Resize frames for faster processing
        
        logger.info(f"Initialized Face Detection System")
        logger.info(f"Recognition threshold: {self.recognition_threshold}")
        logger.info(f"Alert cooldown: {self.alert_cooldown} seconds")
        logger.info(f"Email alerts: {'Enabled' if self.email_alerts_enabled else 'Disabled'}")

    def initialize_camera(self):
        """Initialize camera connection"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test camera
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                return False
            
            logger.info(f"Camera {self.camera_index} initialized successfully")
            logger.info(f"Frame size: {frame.shape[1]}x{frame.shape[0]}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False

    def load_known_faces_from_db(self):
        """Load known faces from Django database"""
        try:
            self.known_faces = load_known_faces()
            logger.info(f"Loaded {len(self.known_faces)} known persons from database")
            
            total_encodings = sum(len(encodings) for encodings in self.known_faces.values())
            logger.info(f"Total face encodings: {total_encodings}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
            return False

    def process_frame(self, frame):
        """Process a single frame for face detection and recognition"""
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=self.resize_factor, fy=self.resize_factor)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame)
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
                
                # Try to recognize face
                best_match = None
                best_confidence = 0.0
                
                for person_name, person_encodings in self.known_faces.items():
                    is_match, match_index, confidence = compare_faces(
                        person_encodings, face_encoding, self.recognition_threshold
                    )
                    
                    if is_match and confidence > best_confidence:
                        best_match = person_name
                        best_confidence = confidence
                
                # Create detection result
                detection = {
                    'face_location': scaled_location,
                    'person_name': best_match,
                    'confidence_score': best_confidence,
                    'is_recognized': best_match is not None,
                    'face_encoding': face_encoding
                }
                
                detections.append(detection)
                
                # Log detection to database for unknown faces
                if not detection['is_recognized']:
                    self.log_unknown_detection(frame, detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return []

    def log_unknown_detection(self, frame, detection):
        """Log unknown face detection to database"""
        try:
            # Check cooldown period
            current_time = datetime.now()
            cooldown_key = f"unknown_{detection['face_location']}"
            
            if cooldown_key in self.last_alert_time:
                time_diff = current_time - self.last_alert_time[cooldown_key]
                if time_diff.total_seconds() < self.alert_cooldown:
                    return  # Still in cooldown period
            
            # Crop face image
            top, right, bottom, left = detection['face_location']
            face_crop = frame[top:bottom, left:right]
            
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
            
        except Exception as e:
            logger.error(f"Error logging unknown detection: {e}")

    def log_recognized_detection(self, person_name, confidence_score):
        """Log recognized face detection"""
        try:
            api_data = {
                'detection_type': 'recognized',
                'person_name': person_name,
                'confidence_score': confidence_score,
                'image_data': None,
                'notes': f"Recognized {person_name} with confidence {confidence_score:.3f}"
            }
            
            # Send to Django API (async)
            threading.Thread(target=self.send_to_api, args=(api_data,)).start()
            
        except Exception as e:
            logger.error(f"Error logging recognized detection: {e}")

    def send_to_api(self, data):
        """Send detection data to Django API"""
        try:
            response = requests.post(self.api_url, json=data, timeout=5)
            
            if response.status_code == 200:
                logger.debug("Detection logged to database successfully")
            else:
                logger.warning(f"API request failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to API: {e}")

    def draw_detections(self, frame, detections):
        """Draw bounding boxes and labels on frame"""
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
                confidence_text = ""
            
            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw label text
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, label + confidence_text, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
        
        return frame

    def add_overlay_info(self, frame):
        """Add system information overlay to frame"""
        height, width = frame.shape[:2]
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add system status
        status_text = f"Known Persons: {len(self.known_faces)} | Threshold: {self.recognition_threshold}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add instructions
        cv2.putText(frame, "Press 'q' to quit, 'r' to reload faces", (10, height - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame

    def reload_settings(self):
        """Reload settings from database"""
        try:
            self.recognition_threshold = float(get_system_setting('recognition_threshold', '0.6'))
            self.alert_cooldown = int(get_system_setting('alert_cooldown', '300'))
            self.email_alerts_enabled = get_system_setting('email_alerts', 'True') == 'True'
            
            logger.info("Settings reloaded from database")
            logger.info(f"Recognition threshold: {self.recognition_threshold}")
            logger.info(f"Alert cooldown: {self.alert_cooldown} seconds")
            
        except Exception as e:
            logger.error(f"Error reloading settings: {e}")

    def run(self):
        """Main detection loop"""
        if not self.initialize_camera():
            logger.error("Failed to initialize camera. Exiting.")
            return False
        
        if not self.load_known_faces_from_db():
            logger.error("Failed to load known faces. Exiting.")
            return False
        
        self.running = True
        logger.info("Starting face detection system...")
        logger.info("Press 'q' to quit, 'r' to reload faces, 's' to reload settings")
        
        fps_counter = 0
        fps_start_time = time.time()
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.error("Failed to read frame from camera")
                    break
                
                # Skip frames for performance
                self.frame_counter += 1
                if self.frame_counter % self.frame_skip != 0:
                    cv2.imshow('Face Detection System', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                
                # Process frame
                detections = self.process_frame(frame)
                
                # Log recognized detections occasionally (to avoid spam)
                for detection in detections:
                    if detection['is_recognized'] and fps_counter % 30 == 0:  # Every 30 processed frames
                        self.log_recognized_detection(detection['person_name'], detection['confidence_score'])
                
                # Draw detections
                display_frame = self.draw_detections(frame.copy(), detections)
                display_frame = self.add_overlay_info(display_frame)
                
                # Show frame
                cv2.imshow('Face Detection System', display_frame)
                
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
                    self.reload_settings()
                
                # Calculate FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps_end_time = time.time()
                    fps = 30 / (fps_end_time - fps_start_time)
                    logger.info(f"Processing FPS: {fps:.2f}")
                    fps_start_time = fps_end_time
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        finally:
            self.cleanup()
        
        return True

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        logger.info("Face detection system stopped")

def main():
    parser = argparse.ArgumentParser(description='Face Detection and Recognition System')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--api-url', type=str, default='http://127.0.0.1:8000/api/detection/', 
                       help='Django API URL (default: http://127.0.0.1:8000/api/detection/)')
    parser.add_argument('--no-display', action='store_true', help='Run without display (headless mode)')
    
    args = parser.parse_args()
    
    # Create and run detection system
    detector = FaceDetectionSystem(camera_index=args.camera, api_url=args.api_url)
    
    try:
        success = detector.run()
        if success:
            logger.info("Face detection system completed successfully")
        else:
            logger.error("Face detection system failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Failed to start face detection system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
