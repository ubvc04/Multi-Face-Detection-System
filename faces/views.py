from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import Person, FaceEncoding, DetectionLog, SystemSettings
from .utils import (
    extract_face_encoding, extract_face_encoding_with_validation, 
    send_alert_email, load_known_faces, compare_faces, 
    check_face_duplicate, capture_face_from_webcam
)
import json
import logging
import base64
import io
import random
from PIL import Image
import numpy as np
import cv2
import threading
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Global camera instance for video streaming
camera_instance = None
camera_lock = threading.Lock()

def login_view(request):
    """User login view with OTP verification"""
    if request.method == 'POST':
        action = request.POST.get('action', 'request_otp')
        
        if action == 'request_otp':
            # Step 1: Request OTP
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Generate 6-digit OTP
                otp = str(random.randint(100000, 999999))
                
                # Store OTP and user info in session
                request.session['login_otp'] = otp
                request.session['login_user_id'] = user.id
                request.session['login_otp_created_at'] = timezone.now().isoformat()
                
                # Send OTP email
                try:
                    send_mail(
                        subject='Login Verification Code - Face Detection System',
                        message=f'Hello {user.username},\n\nYour login verification code is: {otp}\n\nThis code will expire in 5 minutes.\n\nLogin Time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}\n\nIf you didn\'t attempt to log in, please secure your account immediately.\n\nBest regards,\nFace Detection System',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    return JsonResponse({
                        'success': True, 
                        'message': 'OTP sent to your email.',
                        'email': user.email[:3] + '***' + user.email[user.email.index('@'):]
                    })
                except Exception as e:
                    logger.error(f"Failed to send login OTP: {e}")
                    return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid username or password.'})
        
        elif action == 'verify_otp':
            # Step 2: Verify OTP and login automatically
            otp_entered = request.POST.get('otp')
            
            # Get data from session
            stored_otp = request.session.get('login_otp')
            user_id = request.session.get('login_user_id')
            otp_created_at = request.session.get('login_otp_created_at')
            
            if not all([stored_otp, user_id, otp_created_at]):
                return JsonResponse({'success': False, 'message': 'Session expired. Please start again.'})
            
            # Check OTP expiration (5 minutes)
            otp_time = datetime.fromisoformat(otp_created_at)
            if timezone.now() - otp_time > timedelta(minutes=5):
                # Clear session data
                request.session.pop('login_otp', None)
                request.session.pop('login_user_id', None)
                request.session.pop('login_otp_created_at', None)
                return JsonResponse({'success': False, 'message': 'OTP expired. Please login again.'})
            
            # Verify OTP
            if otp_entered == stored_otp:
                try:
                    user = User.objects.get(id=user_id)
                    login(request, user)
                    
                    # Clear session data
                    del request.session['login_otp']
                    del request.session['login_user_id']
                    del request.session['login_otp_created_at']
                    
                    # Send login notification email
                    try:
                        send_mail(
                            subject='Login Notification - Face Detection System',
                            message=f'Hello {user.username},\n\nYou have successfully logged in to the Face Detection System.\n\nLogin Time: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}\n\nIf this wasn\'t you, please contact the administrator immediately.\n\nBest regards,\nFace Detection System',
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[user.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send login notification: {e}")
                    
                    return JsonResponse({'success': True, 'message': 'Login successful!', 'redirect': '/dashboard/'})
                    
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'User not found. Please try again.'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
    
    return render(request, 'faces/login.html')

def signup_view(request):
    """User signup view with OTP verification"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_otp':
            # Step 1: Send OTP to email
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            # Validate inputs
            if not username or not email or not password:
                return JsonResponse({'success': False, 'message': 'All fields are required.'})
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists.'})
            
            # Check if email exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already registered.'})
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP and user data in session
            request.session['signup_otp'] = otp
            request.session['signup_username'] = username
            request.session['signup_email'] = email
            request.session['signup_password'] = password
            request.session['otp_created_at'] = timezone.now().isoformat()
            
            # Send OTP email
            try:
                send_mail(
                    subject='Verify Your Email - Face Detection System',
                    message=f'Hello {username},\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you didn\'t request this, please ignore this email.\n\nBest regards,\nFace Detection System',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                return JsonResponse({'success': True, 'message': 'OTP sent to your email.'})
            except Exception as e:
                logger.error(f"Failed to send OTP email: {e}")
                return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
        
        elif action == 'verify_otp':
            # Step 2: Verify OTP, create user and auto-login
            otp_entered = request.POST.get('otp')
            
            # Get data from session
            stored_otp = request.session.get('signup_otp')
            username = request.session.get('signup_username')
            email = request.session.get('signup_email')
            password = request.session.get('signup_password')
            otp_created_at = request.session.get('otp_created_at')
            
            if not all([stored_otp, username, email, password, otp_created_at]):
                return JsonResponse({'success': False, 'message': 'Session expired. Please start again.'})
            
            # Check OTP expiration (10 minutes)
            otp_time = datetime.fromisoformat(otp_created_at)
            if timezone.now() - otp_time > timedelta(minutes=10):
                return JsonResponse({'success': False, 'message': 'OTP expired. Please request a new one.'})
            
            # Verify OTP
            if otp_entered == stored_otp:
                # Create user
                try:
                    # Double-check email doesn't exist
                    if User.objects.filter(email=email).exists():
                        return JsonResponse({'success': False, 'message': 'Email already registered.'})
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password
                    )
                    
                    # Clear session data
                    del request.session['signup_otp']
                    del request.session['signup_username']
                    del request.session['signup_email']
                    del request.session['signup_password']
                    del request.session['otp_created_at']
                    
                    # Auto-login the user
                    login(request, user)
                    
                    # Send welcome email
                    try:
                        send_mail(
                            subject='Welcome to Face Detection System',
                            message=f'Hello {username},\n\nWelcome to the Face Detection System!\n\nYour account has been successfully created and you are now logged in.\n\nYou can now start using the system to register faces and monitor detections.\n\nBest regards,\nFace Detection System',
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        logger.error(f"Failed to send welcome email: {e}")
                    
                    return JsonResponse({'success': True, 'message': 'Account created successfully!', 'redirect': '/dashboard/'})
                    
                except Exception as e:
                    logger.error(f"Error creating user: {e}")
                    return JsonResponse({'success': False, 'message': 'Error creating account. Please try again.'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP. Please try again.'})
    
    return render(request, 'faces/signup.html')

@csrf_exempt
def check_username_availability(request):
    """Check if username is available"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            
            if not username:
                return JsonResponse({'available': False, 'message': 'Username is required.'})
            
            if len(username) < 3:
                return JsonResponse({'available': False, 'message': 'Username must be at least 3 characters.'})
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({'available': False, 'message': 'Username already taken.'})
            
            return JsonResponse({'available': True, 'message': 'Username is available!'})
            
        except Exception as e:
            logger.error(f"Error checking username: {e}")
            return JsonResponse({'available': False, 'message': 'Error checking username.'})
    
    return JsonResponse({'available': False, 'message': 'Invalid request method.'})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """Main dashboard view with live camera feed"""
    # Get statistics
    total_persons = Person.objects.filter(is_active=True).count()
    total_encodings = FaceEncoding.objects.count()
    recent_detections = DetectionLog.objects.order_by('-detection_time')[:10]
    unknown_detections_today = DetectionLog.objects.filter(
        detection_type='unknown',
        detection_time__date=timezone.now().date()
    ).count()
    
    # Get system settings
    recognition_threshold = SystemSettings.get_setting('recognition_threshold', '0.45')
    email_alerts_enabled = SystemSettings.get_setting('email_alerts', 'True') == 'True'
    
    context = {
        'total_persons': total_persons,
        'total_encodings': total_encodings,
        'recent_detections': recent_detections,
        'unknown_detections_today': unknown_detections_today,
        'recognition_threshold': recognition_threshold,
        'email_alerts_enabled': email_alerts_enabled,
    }
    return render(request, 'faces/dashboard.html', context)

@login_required
def person_list(request):
    """List all registered persons"""
    search_query = request.GET.get('search', '')
    persons = Person.objects.filter(is_active=True)
    
    if search_query:
        persons = persons.filter(name__icontains=search_query)
    
    persons = persons.order_by('name')
    
    # Pagination
    paginator = Paginator(persons, 12)  # 12 persons per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'faces/person_list.html', context)

@login_required
def person_detail(request, person_id):
    """View details of a specific person"""
    person = get_object_or_404(Person, id=person_id)
    face_encodings = person.faceencoding_set.all()
    detection_logs = DetectionLog.objects.filter(person=person).order_by('-detection_time')[:20]
    
    context = {
        'person': person,
        'face_encodings': face_encodings,
        'detection_logs': detection_logs,
    }
    return render(request, 'faces/person_detail.html', context)

@login_required
def register_face(request):
    """Enhanced face registration with webcam capture and duplicate detection"""
    if request.method == 'POST':
        registration_method = request.POST.get('registration_method', 'upload')
        name = request.POST.get('name', '').strip()
        
        if not name:
            messages.error(request, 'Please enter a name.')
            return render(request, 'faces/register_face.html')
        
        # Check if person already exists
        person, created = Person.objects.get_or_create(
            name=name,
            defaults={'is_active': True}
        )
        
        if not created and person.is_active:
            messages.warning(request, f'Person "{name}" already exists. Adding new face encoding.')
        
        successful_encodings = 0
        failed_encodings = 0
        
        if registration_method == 'webcam':
            # Webcam capture method
            try:
                encoding, image_base64, error = capture_face_from_webcam()
                
                if error:
                    messages.error(request, error)
                    return render(request, 'faces/register_face.html')
                
                if encoding is not None:
                    # Check for duplicates
                    is_duplicate, duplicate_person, confidence = check_face_duplicate(encoding)
                    
                    if is_duplicate:
                        messages.error(request, 
                            f'⚠️ This face already exists in the database as "{duplicate_person}" '
                            f'(similarity: {confidence:.1%}). Cannot register duplicate face.')
                        return render(request, 'faces/register_face.html')
                    
                    # Create face encoding from webcam capture
                    import io
                    import base64
                    from django.core.files.base import ContentFile
                    
                    # Decode base64 image
                    image_data = base64.b64decode(image_base64)
                    image_file = ContentFile(image_data, name=f'{name}_webcam_capture.jpg')
                    
                    face_encoding = FaceEncoding(
                        person=person,
                        image=image_file,
                        confidence_score=1.0
                    )
                    face_encoding.set_encoding_array(encoding)
                    face_encoding.save()
                    successful_encodings = 1
                    
                    logger.info(f"Successfully registered face for {name} via webcam capture")
                else:
                    failed_encodings = 1
                    messages.error(request, 'Failed to capture face from webcam.')
                    
            except Exception as e:
                failed_encodings = 1
                logger.error(f"Error in webcam registration: {str(e)}")
                messages.error(request, f'Webcam capture failed: {str(e)}')
        
        else:
            # File upload method
            uploaded_files = request.FILES.getlist('face_images')
            
            if not uploaded_files:
                messages.error(request, 'Please upload at least one face image.')
                return render(request, 'faces/register_face.html')
            
            for uploaded_file in uploaded_files:
                try:
                    # Enhanced face encoding extraction
                    encoding, face_count, error_msg = extract_face_encoding_with_validation(uploaded_file)
                    
                    if error_msg:
                        messages.error(request, f'{uploaded_file.name}: {error_msg}')
                        failed_encodings += 1
                        continue
                    
                    if encoding is not None:
                        # Check for duplicates
                        is_duplicate, duplicate_person, confidence = check_face_duplicate(encoding)
                        
                        if is_duplicate:
                            messages.error(request, 
                                f'⚠️ Face in "{uploaded_file.name}" already exists as "{duplicate_person}" '
                                f'(similarity: {confidence:.1%}). Skipping duplicate.')
                            failed_encodings += 1
                            continue
                        
                        # Save face encoding
                        face_encoding = FaceEncoding(
                            person=person,
                            image=uploaded_file,
                            confidence_score=1.0
                        )
                        face_encoding.set_encoding_array(encoding)
                        face_encoding.save()
                        successful_encodings += 1
                        logger.info(f"Successfully registered face for {name}: {uploaded_file.name}")
                    else:
                        failed_encodings += 1
                        
                except Exception as e:
                    failed_encodings += 1
                    logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
                    messages.error(request, f'Error processing {uploaded_file.name}: {str(e)}')
        
        # Final result handling
        if successful_encodings > 0:
            person.is_active = True
            person.save()
            
            if successful_encodings == 1:
                messages.success(request, f'✅ Successfully registered face for "{name}".')
            else:
                messages.success(request, f'✅ Successfully registered {successful_encodings} face images for "{name}".')
            
            if failed_encodings > 0:
                messages.warning(request, f'⚠️ {failed_encodings} image(s) could not be processed.')
                
            return redirect('person_detail', person_id=person.id)
        else:
            messages.error(request, 'No face encodings could be registered. Please try different images or contact support.')
            if not created:
                # If we created a new person but no encodings were successful, delete it
                if person.faceencoding_set.count() == 0:
                    person.delete()
    
    return render(request, 'faces/register_face.html')

@login_required
def detection_logs(request):
    """View detection logs"""
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    logs = DetectionLog.objects.all()
    
    if filter_type != 'all':
        logs = logs.filter(detection_type=filter_type)
    
    if search_query:
        logs = logs.filter(
            Q(person__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    logs = logs.order_by('-detection_time')
    
    # Pagination
    paginator = Paginator(logs, 20)  # 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
        'detection_types': DetectionLog.DETECTION_TYPES,
    }
    return render(request, 'faces/detection_logs.html', context)

@login_required
def delete_person(request, person_id):
    """Delete a person and all their face encodings"""
    if request.method == 'POST':
        person = get_object_or_404(Person, id=person_id)
        person_name = person.name
        person.delete()
        messages.success(request, f'Person "{person_name}" has been deleted successfully.')
        return redirect('person_list')
    
    return redirect('person_list')

@login_required
def delete_face_encoding(request, encoding_id):
    """Delete a specific face encoding"""
    if request.method == 'POST':
        encoding = get_object_or_404(FaceEncoding, id=encoding_id)
        person = encoding.person
        encoding.delete()
        messages.success(request, 'Face encoding deleted successfully.')
        return redirect('person_detail', person_id=person.id)
    
    return redirect('person_list')

@login_required
def system_settings(request):
    """System settings view"""
    if request.method == 'POST':
        # Update settings
        recognition_threshold = request.POST.get('recognition_threshold', '0.45')
        email_alerts = request.POST.get('email_alerts') == 'on'
        alert_cooldown = request.POST.get('alert_cooldown', '300')  # 5 minutes default
        duplicate_threshold = request.POST.get('duplicate_threshold', '0.4')  # New setting
        
        # Validate threshold values
        try:
            threshold_val = float(recognition_threshold)
            if not (0.1 <= threshold_val <= 1.0):
                messages.error(request, 'Recognition threshold must be between 0.1 and 1.0')
                return redirect('system_settings')
        except ValueError:
            messages.error(request, 'Invalid recognition threshold value')
            return redirect('system_settings')
        
        try:
            duplicate_val = float(duplicate_threshold)
            if not (0.1 <= duplicate_val <= 1.0):
                messages.error(request, 'Duplicate threshold must be between 0.1 and 1.0')
                return redirect('system_settings')
        except ValueError:
            messages.error(request, 'Invalid duplicate threshold value')
            return redirect('system_settings')
        
        SystemSettings.set_setting('recognition_threshold', recognition_threshold, 'Face recognition confidence threshold')
        SystemSettings.set_setting('email_alerts', str(email_alerts), 'Enable/disable email alerts')
        SystemSettings.set_setting('alert_cooldown', alert_cooldown, 'Cooldown period between alerts (seconds)')
        SystemSettings.set_setting('duplicate_threshold', duplicate_threshold, 'Threshold for detecting duplicate faces during registration')
        
        messages.success(request, 'Settings updated successfully.')
        return redirect('system_settings')
    
    # Get current settings
    current_settings = {
        'recognition_threshold': float(SystemSettings.get_setting('recognition_threshold', '0.45')),
        'email_alerts': SystemSettings.get_setting('email_alerts', 'True') == 'True',
        'alert_cooldown': int(SystemSettings.get_setting('alert_cooldown', '300')),
        'duplicate_threshold': float(SystemSettings.get_setting('duplicate_threshold', '0.4')),
    }
    
    context = {
        'settings': current_settings,
    }
    return render(request, 'faces/system_settings.html', context)

# API endpoint for the detection script
@csrf_exempt
def detection_api(request):
    """API endpoint for the detection script to log detections"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            detection_type = data.get('detection_type', 'unknown')
            person_name = data.get('person_name')
            confidence_score = data.get('confidence_score')
            image_data = data.get('image_data')  # base64 encoded image
            notes = data.get('notes', '')
            
            # Get person object if recognized
            person = None
            if detection_type == 'recognized' and person_name:
                try:
                    person = Person.objects.get(name=person_name, is_active=True)
                except Person.DoesNotExist:
                    pass
            
            # Create detection log
            detection_log = DetectionLog(
                person=person,
                detection_type=detection_type,
                confidence_score=confidence_score,
                notes=notes
            )
            
            # Save image if provided
            if image_data:
                try:
                    # Decode base64 image
                    image_data = image_data.split(',')[1] if ',' in image_data else image_data
                    image_binary = base64.b64decode(image_data)
                    image_file = ContentFile(image_binary, name=f'detection_{detection_log.detection_time.strftime("%Y%m%d_%H%M%S")}.jpg')
                    detection_log.image_snapshot = image_file
                except Exception as e:
                    logger.error(f"Error processing image data: {e}")
            
            detection_log.save()
            
            # Send email alert for unknown faces
            if detection_type == 'unknown' and SystemSettings.get_setting('email_alerts', 'True') == 'True':
                try:
                    send_alert_email(detection_log)
                    detection_log.email_sent = True
                    detection_log.save()
                except Exception as e:
                    logger.error(f"Error sending email alert: {e}")
            
            return JsonResponse({'status': 'success', 'log_id': detection_log.id})
            
        except Exception as e:
            logger.error(f"Error in detection API: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

class CameraStreamer:
    """Camera streaming class for HTTP video feed"""
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.camera = None
        self.is_active = False
        self.known_faces = {}
        self.recognition_threshold = 0.6
        self.unknown_face_tracker = {}  # Track unknown faces by location
        self.unknown_face_cooldown = {}  # Cooldown to avoid duplicate saves
        
    def initialize(self):
        """Initialize camera and load faces"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
                
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Load known faces
            self.known_faces = load_known_faces()
            self.recognition_threshold = float(SystemSettings.get_setting('recognition_threshold', '0.6'))
            
            self.is_active = True
            logger.info(f"Camera {self.camera_index} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def get_frame(self):
        """Get processed frame with face detection"""
        try:
            if not self.camera or not self.is_active:
                return None
                
            ret, frame = self.camera.read()
            if not ret:
                return None
            
            # Process frame for face detection
            detections = self.process_frame(frame)
            
            # Track unknown faces
            self.track_unknown_faces(detections, frame)
            
            # Draw detections
            frame = self.draw_detections(frame, detections)
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None
    
    def track_unknown_faces(self, detections, frame):
        """Track unknown faces and save if seen for at least 1 second"""
        current_time = time.time()
        current_unknown_locations = []
        
        for detection in detections:
            if not detection['is_recognized']:
                location = detection['face_location']
                location_key = f"{location[0]}_{location[1]}_{location[2]}_{location[3]}"
                current_unknown_locations.append(location_key)
                
                # Check if this location is already being tracked
                if location_key not in self.unknown_face_tracker:
                    # Start tracking this unknown face
                    self.unknown_face_tracker[location_key] = {
                        'first_seen': current_time,
                        'last_seen': current_time,
                        'face_location': location,
                        'saved': False
                    }
                else:
                    # Update last seen time
                    self.unknown_face_tracker[location_key]['last_seen'] = current_time
                    tracker = self.unknown_face_tracker[location_key]
                    
                    # Check if face has been visible for at least 1 second and not yet saved
                    duration = current_time - tracker['first_seen']
                    if duration >= 1.0 and not tracker['saved']:
                        # Check cooldown to avoid duplicate saves
                        cooldown_key = f"{location[0]//10}_{location[1]//10}"  # Group similar locations
                        if cooldown_key not in self.unknown_face_cooldown or \
                           (current_time - self.unknown_face_cooldown[cooldown_key]) > 5.0:
                            # Save the unknown face
                            self.save_unknown_face(frame, location, duration)
                            tracker['saved'] = True
                            self.unknown_face_cooldown[cooldown_key] = current_time
        
        # Clean up old tracking data (faces that disappeared)
        keys_to_remove = []
        for key in list(self.unknown_face_tracker.keys()):
            if key not in current_unknown_locations:
                # Face disappeared, check if it was visible long enough but not saved
                tracker = self.unknown_face_tracker[key]
                duration = tracker['last_seen'] - tracker['first_seen']
                if duration >= 1.0 and not tracker['saved']:
                    # Face was there for 1+ seconds, save it before removing
                    top, right, bottom, left = tracker['face_location']
                    if top >= 0 and left >= 0 and bottom <= frame.shape[0] and right <= frame.shape[1]:
                        self.save_unknown_face(frame, tracker['face_location'], duration)
                
                keys_to_remove.append(key)
        
        # Remove disappeared faces from tracker
        for key in keys_to_remove:
            del self.unknown_face_tracker[key]
    
    def save_unknown_face(self, frame, face_location, duration):
        """Save unknown face to database"""
        try:
            top, right, bottom, left = face_location
            
            # Extract face region with some padding
            padding = 20
            top = max(0, top - padding)
            left = max(0, left - padding)
            bottom = min(frame.shape[0], bottom + padding)
            right = min(frame.shape[1], right + padding)
            
            face_image = frame[top:bottom, left:right]
            
            # Convert BGR to RGB
            face_image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            from PIL import Image
            pil_image = Image.fromarray(face_image_rgb)
            
            # Save to BytesIO
            img_io = io.BytesIO()
            pil_image.save(img_io, format='JPEG', quality=90)
            img_io.seek(0)
            
            # Create detection log
            detection_log = DetectionLog(
                person=None,
                detection_type='unknown',
                confidence_score=0.0,
                notes=f'Detected for {duration:.1f} seconds',
                email_sent=False
            )
            
            # Save image
            from django.core.files.base import ContentFile
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S_%f")
            image_file = ContentFile(img_io.getvalue(), name=f'unknown_{timestamp}.jpg')
            detection_log.image_snapshot = image_file
            detection_log.save()
            
            logger.info(f"Saved unknown face (duration: {duration:.1f}s) - ID: {detection_log.id}")
            
            # Send email alert if enabled
            if SystemSettings.get_setting('email_alerts', 'True') == 'True':
                try:
                    send_alert_email(detection_log)
                    detection_log.email_sent = True
                    detection_log.save()
                except Exception as e:
                    logger.error(f"Error sending email alert: {e}")
                    
        except Exception as e:
            logger.error(f"Error saving unknown face: {e}")
    
    def process_frame(self, frame):
        """Process frame for face detection and recognition"""
        try:
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            import face_recognition
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
    
    def release(self):
        """Release camera resources"""
        self.is_active = False
        if self.camera:
            self.camera.release()

def generate_frames():
    """Generator function for video streaming"""
    global camera_instance
    
    with camera_lock:
        if camera_instance is None:
            camera_instance = CameraStreamer(camera_index=0)
            if not camera_instance.initialize():
                return
    
    while True:
        try:
            frame = camera_instance.get_frame()
            if frame is None:
                break
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            logger.error(f"Error generating frame: {e}")
            break

@login_required
def camera_feed(request):
    """Video streaming endpoint"""
    try:
        return StreamingHttpResponse(generate_frames(),
                                   content_type='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Error in camera feed: {e}")
        return HttpResponse("Camera feed error", status=500)

@login_required
def camera_control(request):
    """Camera control API endpoint"""
    global camera_instance
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'start':
                with camera_lock:
                    if camera_instance is None:
                        camera_instance = CameraStreamer(camera_index=data.get('camera_index', 0))
                        if camera_instance.initialize():
                            return JsonResponse({'status': 'success', 'message': 'Camera started'})
                        else:
                            camera_instance = None
                            return JsonResponse({'status': 'error', 'message': 'Failed to start camera'})
                    else:
                        return JsonResponse({'status': 'success', 'message': 'Camera already running'})
            
            elif action == 'stop':
                with camera_lock:
                    if camera_instance:
                        camera_instance.release()
                        camera_instance = None
                        return JsonResponse({'status': 'success', 'message': 'Camera stopped'})
                    else:
                        return JsonResponse({'status': 'success', 'message': 'Camera already stopped'})
            
            elif action == 'reload_faces':
                if camera_instance:
                    camera_instance.known_faces = load_known_faces()
                    camera_instance.recognition_threshold = float(SystemSettings.get_setting('recognition_threshold', '0.6'))
                    return JsonResponse({'status': 'success', 'message': 'Faces reloaded', 'count': len(camera_instance.known_faces)})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Camera not active'})
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'})
                
        except Exception as e:
            logger.error(f"Error in camera control: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def camera_status(request):
    """Get camera status"""
    global camera_instance
    
    with camera_lock:
        is_active = camera_instance is not None and camera_instance.is_active
        known_faces_count = len(camera_instance.known_faces) if camera_instance else 0
    
    return JsonResponse({
        'status': 'success',
        'camera_active': is_active,
        'known_faces_count': known_faces_count,
        'timestamp': datetime.now().isoformat()
    })

@login_required
def get_unknown_faces(request):
    """Get recently detected unknown faces"""
    try:
        # Get unknown faces from the last 5 minutes
        time_threshold = timezone.now() - timedelta(minutes=5)
        unknown_faces = DetectionLog.objects.filter(
            detection_type='unknown',
            detection_time__gte=time_threshold
        ).order_by('-detection_time')[:20]
        
        faces_data = []
        for face in unknown_faces:
            faces_data.append({
                'id': face.id,
                'image_url': face.image_snapshot.url if face.image_snapshot else '',
                'time': face.detection_time.strftime('%H:%M:%S'),
                'confidence': f"{face.confidence_score:.2f}" if face.confidence_score else None,
                'email_sent': face.email_sent,
                'duration': face.notes if 'second' in face.notes else None
            })
        
        return JsonResponse({
            'status': 'success',
            'unknown_faces': faces_data
        })
    except Exception as e:
        logger.error(f"Error getting unknown faces: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
