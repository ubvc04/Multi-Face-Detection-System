import face_recognition
import numpy as np
import cv2
from PIL import Image
import io
import logging
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import os

logger = logging.getLogger(__name__)

def extract_face_encoding(image_file):
    """
    Extract face encoding from uploaded image file
    Returns numpy array of face encoding or None if no face found
    """
    try:
        # Read image file
        image_file.seek(0)  # Reset file pointer
        image_data = image_file.read()
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert PIL image to numpy array
        image_array = np.array(pil_image)
        
        # Find face locations
        face_locations = face_recognition.face_locations(image_array)
        
        if len(face_locations) == 0:
            logger.warning("No face found in the uploaded image")
            return None
        
        if len(face_locations) > 1:
            logger.warning(f"Multiple faces found ({len(face_locations)}), using the first one")
        
        # Extract face encodings
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) == 0:
            logger.warning("Could not extract face encoding from the image")
            return None
        
        # Return the first face encoding
        return face_encodings[0]
        
    except Exception as e:
        logger.error(f"Error extracting face encoding: {str(e)}")
        return None

def compare_faces(known_encodings, unknown_encoding, tolerance=0.6):
    """
    Enhanced face comparison with improved accuracy for multiple faces
    Returns (is_match, best_match_index, confidence_score)
    """
    try:
        if not known_encodings or unknown_encoding is None:
            return False, -1, 0.0
        
        # Convert known encodings to numpy arrays if they're lists
        known_arrays = []
        for encoding in known_encodings:
            if isinstance(encoding, list):
                known_arrays.append(np.array(encoding))
            else:
                known_arrays.append(encoding)
        
        # Calculate face distances for all known encodings
        face_distances = face_recognition.face_distance(known_arrays, unknown_encoding)
        
        # Find the best (minimum distance) match
        best_match_index = np.argmin(face_distances)
        best_distance = face_distances[best_match_index]
        
        # Convert distance to confidence score (lower distance = higher confidence)
        # Use a more precise conversion formula
        confidence_score = max(0.0, 1.0 - (best_distance / 1.0))
        
        # More strict threshold checking - only accept very close matches
        is_match = best_distance <= tolerance
        
        # Additional validation: ensure confidence is above minimum threshold
        min_confidence_threshold = 0.5  # Minimum 50% confidence required
        if confidence_score < min_confidence_threshold:
            is_match = False
        
        logger.debug(f"Face comparison - Distance: {best_distance:.3f}, Confidence: {confidence_score:.3f}, Match: {is_match}")
        
        return is_match, best_match_index, confidence_score
        
    except Exception as e:
        logger.error(f"Error comparing faces: {str(e)}")
        return False, -1, 0.0

def send_alert_email(detection_log, recipient_email=None):
    """
    Send email alert for unknown face detection
    Sends from host email (settings.EMAIL_HOST_USER) to recipient_email
    """
    try:
        # Check if email is configured
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured, skipping alert")
            return False
        
        # If no recipient email provided, skip sending
        if not recipient_email:
            logger.warning("No recipient email provided, skipping alert")
            return False
        
        subject = f"Security Alert: Unknown Face Detected"
        
        # Prepare context for email template
        context = {
            'detection_log': detection_log,
            'detection_time': detection_log.detection_time.strftime('%Y-%m-%d %H:%M:%S'),
            'site_name': 'Face Detection Security System',
        }
        
        # Render email content
        html_content = render_to_string('faces/email/alert_email.html', context)
        text_content = f"""
Security Alert: Unknown Face Detected

Detection Time: {context['detection_time']}
Detection Type: {detection_log.get_detection_type_display()}
Confidence Score: {detection_log.confidence_score or 'N/A'}

Notes: {detection_log.notes or 'None'}

This is an automated alert from the Face Detection Security System.
        """
        
        # Create email - Send FROM host email TO user email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_HOST_USER,  # From: baveshchowdary1@gmail.com
            to=[recipient_email],  # To: logged-in user's email
        )
        
        # Attach image if available
        if detection_log.image_snapshot:
            try:
                email.attach_file(detection_log.image_snapshot.path)
            except Exception as e:
                logger.error(f"Error attaching image to email: {e}")
        
        # Send email
        email.send()
        logger.info(f"Alert email sent for detection log {detection_log.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending alert email: {str(e)}")
        return False

def process_camera_frame(frame, known_faces_data, recognition_threshold=0.6):
    """
    Process a camera frame to detect and recognize faces
    Returns list of detection results
    """
    try:
        # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        detection_results = []
        
        for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
            # Compare with known faces
            best_match = None
            best_confidence = 0.0
            
            for person_name, person_encodings in known_faces_data.items():
                is_match, match_index, confidence = compare_faces(person_encodings, face_encoding, recognition_threshold)
                
                if is_match and confidence > best_confidence:
                    best_match = person_name
                    best_confidence = confidence
            
            # Prepare detection result
            result = {
                'face_location': face_location,
                'person_name': best_match,
                'confidence_score': best_confidence,
                'is_recognized': best_match is not None,
                'face_encoding': face_encoding
            }
            
            detection_results.append(result)
        
        return detection_results
        
    except Exception as e:
        logger.error(f"Error processing camera frame: {str(e)}")
        return []

def crop_face_from_frame(frame, face_location):
    """
    Crop face from frame using face location
    Returns cropped face image as numpy array
    """
    try:
        top, right, bottom, left = face_location
        
        # Add some padding
        padding = 20
        top = max(0, top - padding)
        bottom = min(frame.shape[0], bottom + padding)
        left = max(0, left - padding)
        right = min(frame.shape[1], right + padding)
        
        # Crop face
        face_crop = frame[top:bottom, left:right]
        
        return face_crop
        
    except Exception as e:
        logger.error(f"Error cropping face: {str(e)}")
        return None

def save_detection_snapshot(frame, face_location, filename):
    """
    Save a snapshot of detected face
    Returns saved file path or None
    """
    try:
        # Crop face
        face_crop = crop_face_from_frame(frame, face_location)
        
        if face_crop is not None:
            # Create snapshots directory if it doesn't exist
            snapshots_dir = os.path.join(settings.MEDIA_ROOT, 'detection_snapshots')
            os.makedirs(snapshots_dir, exist_ok=True)
            
            # Save image
            file_path = os.path.join(snapshots_dir, filename)
            cv2.imwrite(file_path, face_crop)
            
            # Return relative path for database storage
            relative_path = os.path.join('detection_snapshots', filename)
            return relative_path
            
    except Exception as e:
        logger.error(f"Error saving detection snapshot: {str(e)}")
        
    return None

def load_known_faces():
    """
    Load all known faces from database
    Returns dictionary with person names as keys and list of encodings as values
    """
    try:
        from .models import Person, FaceEncoding
        
        known_faces = {}
        
        for person in Person.objects.filter(is_active=True).prefetch_related('faceencoding_set'):
            encodings = []
            for face_encoding in person.faceencoding_set.all():
                encoding_array = face_encoding.get_encoding_array()
                if encoding_array is not None:
                    encodings.append(np.array(encoding_array))
            
            if encodings:
                known_faces[person.name] = encodings
        
        logger.info(f"Loaded {len(known_faces)} known persons with face encodings")
        return known_faces
        
    except Exception as e:
        logger.error(f"Error loading known faces: {str(e)}")
        return {}

def check_face_duplicate(new_encoding, duplicate_threshold=0.4):
    """
    Check if a face encoding already exists in the database
    Returns (is_duplicate, person_name, confidence) if duplicate found
    """
    try:
        from .models import Person, FaceEncoding
        
        if new_encoding is None:
            return False, None, 0.0
        
        # Convert to numpy array if needed
        if isinstance(new_encoding, list):
            new_encoding = np.array(new_encoding)
        
        # Check against all existing face encodings
        for person in Person.objects.filter(is_active=True).prefetch_related('faceencoding_set'):
            for face_encoding in person.faceencoding_set.all():
                existing_encoding = face_encoding.get_encoding_array()
                if existing_encoding is not None:
                    existing_array = np.array(existing_encoding)
                    
                    # Calculate distance
                    distance = face_recognition.face_distance([existing_array], new_encoding)[0]
                    confidence = max(0.0, 1.0 - distance)
                    
                    # If very similar (distance < threshold), it's a duplicate
                    if distance < duplicate_threshold:
                        logger.info(f"Duplicate face detected for {person.name} - Distance: {distance:.3f}, Confidence: {confidence:.3f}")
                        return True, person.name, confidence
        
        return False, None, 0.0
        
    except Exception as e:
        logger.error(f"Error checking face duplicate: {str(e)}")
        return False, None, 0.0

def extract_face_encoding_with_validation(image_file):
    """
    Enhanced face encoding extraction with better validation and error handling
    Returns (encoding, face_count, error_message)
    """
    try:
        # Read image file
        image_file.seek(0)  # Reset file pointer
        image_data = image_file.read()
        
        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert PIL image to numpy array
        image_array = np.array(pil_image)
        
        # Find face locations using more accurate model
        face_locations = face_recognition.face_locations(image_array, model="hog")
        
        if len(face_locations) == 0:
            return None, 0, "No face found in the uploaded image. Please upload a clear photo with a visible face."
        
        if len(face_locations) > 1:
            return None, len(face_locations), f"Multiple faces detected ({len(face_locations)}). Please upload an image with only one face."
        
        # Extract face encodings
        face_encodings = face_recognition.face_encodings(image_array, face_locations, model="large")
        
        if len(face_encodings) == 0:
            return None, 1, "Could not extract face features from the image. Please try a different photo."
        
        # Get the face encoding
        encoding = face_encodings[0]
        
        # Validate encoding quality (check if it's not all zeros or invalid)
        if np.allclose(encoding, 0) or np.any(np.isnan(encoding)):
            return None, 1, "Invalid face encoding extracted. Please try a different photo with better lighting."
        
        return encoding, 1, None
        
    except Exception as e:
        logger.error(f"Error extracting face encoding: {str(e)}")
        return None, 0, f"Error processing image: {str(e)}"

def capture_face_from_webcam():
    """
    Capture face from webcam for registration
    Returns (face_encoding, face_image_base64, error_message)
    """
    try:
        import cv2
        import base64
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            # Try alternative camera indices
            for i in range(1, 5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    break
            else:
                return None, None, "Could not access camera. Please check if the camera is connected and not being used by another application."
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        logger.info("Camera initialized for face capture. Press SPACE to capture, ESC to cancel.")
        
        best_frame = None
        best_encoding = None
        
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Convert to RGB for face detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            display_frame = frame.copy()
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face detected - Press SPACE to capture", 
                           (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add instructions
            cv2.putText(display_frame, "Position face in frame, press SPACE to capture, ESC to cancel", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Face Capture for Registration', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 32:  # SPACE key
                if len(face_locations) == 1:
                    # Extract encoding
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if face_encodings:
                        best_encoding = face_encodings[0]
                        best_frame = frame
                        break
                elif len(face_locations) == 0:
                    logger.warning("No face detected. Please position your face in the frame.")
                else:
                    logger.warning("Multiple faces detected. Please ensure only one person is in the frame.")
            
            elif key == 27:  # ESC key
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if best_encoding is not None and best_frame is not None:
            # Convert frame to base64 for storage
            _, buffer = cv2.imencode('.jpg', best_frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return best_encoding, image_base64, None
        else:
            return None, None, "Face capture was cancelled or failed."
            
    except Exception as e:
        logger.error(f"Error capturing face from webcam: {str(e)}")
        return None, None, f"Error accessing camera: {str(e)}"

def get_system_setting(setting_name, default_value):
    """
    Get system setting value with fallback to default
    """
    try:
        from .models import SystemSettings
        return SystemSettings.get_setting(setting_name, default_value)
    except Exception as e:
        logger.error(f"Error getting system setting {setting_name}: {str(e)}")
        return default_value
