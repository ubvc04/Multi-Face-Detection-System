import json
import base64
import cv2
import asyncio
import threading
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from .models import DetectionLog, Person, SystemSettings
from .utils import load_known_faces, compare_faces
import face_recognition
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class CameraConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = None
        self.is_streaming = False
        self.known_faces = {}
        self.detection_thread = None
        self.recognition_threshold = 0.6
        
    async def connect(self):
        """Handle WebSocket connection"""
        await self.accept()
        logger.info("WebSocket connection established")
        
        # Load known faces
        await self.load_known_faces()
        await self.load_settings()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'status': 'connected',
            'message': 'Camera stream ready'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.is_streaming = False
        if self.camera:
            self.camera.release()
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'start_camera':
                await self.start_camera_stream(data.get('camera_index', 0))
            elif message_type == 'stop_camera':
                await self.stop_camera_stream()
            elif message_type == 'reload_faces':
                await self.load_known_faces()
                await self.send(text_data=json.dumps({
                    'type': 'faces_reloaded',
                    'count': len(self.known_faces)
                }))
            elif message_type == 'reload_settings':
                await self.load_settings()
                await self.send(text_data=json.dumps({
                    'type': 'settings_reloaded',
                    'threshold': self.recognition_threshold
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON data'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def load_known_faces(self):
        """Load known faces from database"""
        try:
            self.known_faces = load_known_faces()
            logger.info(f"Loaded {len(self.known_faces)} known persons")
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
            self.known_faces = {}

    @database_sync_to_async
    def load_settings(self):
        """Load system settings"""
        try:
            self.recognition_threshold = float(SystemSettings.get_setting('recognition_threshold', '0.6'))
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.recognition_threshold = 0.6

    async def start_camera_stream(self, camera_index=0):
        """Start camera streaming"""
        try:
            if self.is_streaming:
                await self.stop_camera_stream()
            
            # Initialize camera
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Failed to open camera {camera_index}'
                }))
                return
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_streaming = True
            
            await self.send(text_data=json.dumps({
                'type': 'camera_started',
                'message': f'Camera {camera_index} started successfully'
            }))
            
            # Start detection in a separate thread
            self.detection_thread = threading.Thread(target=self.camera_detection_loop)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to start camera: {str(e)}'
            }))

    async def stop_camera_stream(self):
        """Stop camera streaming"""
        self.is_streaming = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        await self.send(text_data=json.dumps({
            'type': 'camera_stopped',
            'message': 'Camera stream stopped'
        }))

    def camera_detection_loop(self):
        """Main camera detection loop running in separate thread"""
        frame_count = 0
        process_every_n_frames = 3  # Process every 3rd frame for performance
        
        while self.is_streaming and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Process face detection every N frames
                if frame_count % process_every_n_frames == 0:
                    detections = self.process_frame_for_faces(frame)
                    
                    # Draw detections on frame
                    frame_with_detections = self.draw_detections(frame.copy(), detections)
                    
                    # Send frame with detections
                    asyncio.run_coroutine_threadsafe(
                        self.send_frame_with_detections(frame_with_detections, detections),
                        asyncio.get_event_loop()
                    )
                    
                    # Log detections to database
                    if detections:
                        asyncio.run_coroutine_threadsafe(
                            self.log_detections(frame, detections),
                            asyncio.get_event_loop()
                        )
                else:
                    # Send frame without processing for smooth video
                    asyncio.run_coroutine_threadsafe(
                        self.send_frame(frame),
                        asyncio.get_event_loop()
                    )
                
                # Small delay to prevent overwhelming
                asyncio.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                break

    def process_frame_for_faces(self, frame):
        """Process frame for face detection and recognition"""
        try:
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            detections = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Scale back to original frame size
                top, right, bottom, left = face_location
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                
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
                
                detection = {
                    'face_location': (top, right, bottom, left),
                    'person_name': best_match,
                    'confidence_score': best_confidence,
                    'is_recognized': best_match is not None,
                    'timestamp': datetime.now().isoformat()
                }
                
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return []

    def draw_detections(self, frame, detections):
        """Draw detection boxes and labels on frame"""
        for detection in detections:
            top, right, bottom, left = detection['face_location']
            
            # Choose color and label
            if detection['is_recognized']:
                color = (0, 255, 0)  # Green
                label = detection['person_name']
                confidence_text = f" ({detection['confidence_score']:.2f})"
            else:
                color = (0, 0, 255)  # Red
                label = "Unknown Person"
                confidence_text = ""
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw label text
            cv2.putText(frame, label + confidence_text, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add system info
        info_text = f"Known Persons: {len(self.known_faces)} | Threshold: {self.recognition_threshold}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

    async def send_frame(self, frame):
        """Send frame to WebSocket"""
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            await self.send(text_data=json.dumps({
                'type': 'video_frame',
                'frame': frame_base64,
                'timestamp': datetime.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending frame: {e}")

    async def send_frame_with_detections(self, frame, detections):
        """Send frame with detection data to WebSocket"""
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            await self.send(text_data=json.dumps({
                'type': 'video_frame_with_detections',
                'frame': frame_base64,
                'detections': detections,
                'timestamp': datetime.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending frame with detections: {e}")

    @database_sync_to_async
    def log_detections(self, frame, detections):
        """Log detections to database"""
        try:
            for detection in detections:
                if not detection['is_recognized']:
                    # Only log unknown faces to avoid database spam
                    top, right, bottom, left = detection['face_location']
                    face_crop = frame[top:bottom, left:right]
                    
                    # Encode face crop as image
                    _, buffer = cv2.imencode('.jpg', face_crop)
                    image_file = ContentFile(buffer.tobytes(), 
                                           name=f'unknown_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg')
                    
                    # Create detection log
                    detection_log = DetectionLog(
                        detection_type='unknown',
                        confidence_score=detection['confidence_score'],
                        image_snapshot=image_file,
                        notes=f"Unknown face detected via web interface at {detection['timestamp']}"
                    )
                    detection_log.save()
                    
                    logger.info(f"Logged unknown face detection: {detection_log.id}")
                    
        except Exception as e:
            logger.error(f"Error logging detections: {e}")
