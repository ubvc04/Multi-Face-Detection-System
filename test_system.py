#!/usr/bin/env python
"""
System Test Script for Face Detection Security System
Tests all major components and functionality
"""

import os
import sys
import time
import requests
import json
import subprocess
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_security.settings')
import django
django.setup()

from faces.models import Person, FaceEncoding, DetectionLog, SystemSettings
from django.contrib.auth.models import User

class SystemTester:
    def __init__(self):
        self.test_results = []
        self.server_url = "http://127.0.0.1:8000"
        
    def log_test(self, test_name, result, message=""):
        """Log test result"""
        status = "✅ PASS" if result else "❌ FAIL"
        self.test_results.append({
            'name': test_name,
            'result': result,
            'message': message,
            'status': status
        })
        print(f"{status} {test_name}: {message}")
    
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            # Test basic queries
            person_count = Person.objects.count()
            user_count = User.objects.count()
            
            self.log_test("Database Connection", True, f"Connected - {person_count} persons, {user_count} users")
            return True
        except Exception as e:
            self.log_test("Database Connection", False, f"Error: {str(e)}")
            return False
    
    def test_models(self):
        """Test database models"""
        try:
            # Test Person model
            test_person = Person(name="Test Person", is_active=True)
            test_person.save()
            
            # Test SystemSettings model
            SystemSettings.set_setting('test_setting', 'test_value', 'Test setting')
            value = SystemSettings.get_setting('test_setting')
            
            # Cleanup
            test_person.delete()
            SystemSettings.objects.filter(setting_name='test_setting').delete()
            
            self.log_test("Database Models", True, "All models working correctly")
            return True
        except Exception as e:
            self.log_test("Database Models", False, f"Error: {str(e)}")
            return False
    
    def test_django_server(self):
        """Test if Django server is running"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=5)
            if response.status_code in [200, 302]:  # 302 for redirect to login
                self.log_test("Django Server", True, f"Server responding (Status: {response.status_code})")
                return True
            else:
                self.log_test("Django Server", False, f"Unexpected status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Django Server", False, f"Server not accessible: {str(e)}")
            return False
    
    def test_face_recognition_imports(self):
        """Test face recognition library imports"""
        try:
            import cv2
            import face_recognition
            import numpy as np
            from PIL import Image
            
            # Test OpenCV
            cv2_version = cv2.__version__
            
            # Test basic face_recognition functionality
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            face_locations = face_recognition.face_locations(test_image)
            
            self.log_test("Face Recognition Libraries", True, f"OpenCV {cv2_version}, face_recognition available")
            return True
        except Exception as e:
            self.log_test("Face Recognition Libraries", False, f"Import error: {str(e)}")
            return False
    
    def test_camera_access(self):
        """Test camera accessibility"""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    height, width = frame.shape[:2]
                    cap.release()
                    self.log_test("Camera Access", True, f"Camera accessible - {width}x{height}")
                    return True
                else:
                    cap.release()
                    self.log_test("Camera Access", False, "Camera opened but cannot read frames")
                    return False
            else:
                self.log_test("Camera Access", False, "Cannot open camera")
                return False
        except Exception as e:
            self.log_test("Camera Access", False, f"Error: {str(e)}")
            return False
    
    def test_email_configuration(self):
        """Test email configuration"""
        try:
            from django.conf import settings
            from django.core.mail import EmailMessage
            
            # Check email settings
            if not settings.EMAIL_HOST_USER:
                self.log_test("Email Configuration", False, "EMAIL_HOST_USER not configured")
                return False
            
            if not settings.EMAIL_HOST_PASSWORD:
                self.log_test("Email Configuration", False, "EMAIL_HOST_PASSWORD not configured")
                return False
            
            # Note: We don't actually send a test email to avoid spam
            self.log_test("Email Configuration", True, f"SMTP configured for {settings.EMAIL_HOST_USER}")
            return True
        except Exception as e:
            self.log_test("Email Configuration", False, f"Error: {str(e)}")
            return False
    
    def test_utils_functions(self):
        """Test utility functions"""
        try:
            from faces.utils import load_known_faces, get_system_setting
            
            # Test load_known_faces
            known_faces = load_known_faces()
            
            # Test get_system_setting
            threshold = get_system_setting('recognition_threshold', '0.6')
            
            self.log_test("Utility Functions", True, f"Utils working - {len(known_faces)} known faces")
            return True
        except Exception as e:
            self.log_test("Utility Functions", False, f"Error: {str(e)}")
            return False
    
    def test_api_endpoint(self):
        """Test detection API endpoint"""
        try:
            api_url = f"{self.server_url}/api/detection/"
            
            # Test with invalid data (should return error)
            response = requests.post(api_url, json={}, timeout=5)
            
            # API should be accessible even if data is invalid
            if response.status_code in [200, 400, 500]:
                self.log_test("API Endpoint", True, f"API accessible (Status: {response.status_code})")
                return True
            else:
                self.log_test("API Endpoint", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_admin_user(self):
        """Test admin user exists"""
        try:
            admin_users = User.objects.filter(is_superuser=True)
            if admin_users.exists():
                admin_user = admin_users.first()
                self.log_test("Admin User", True, f"Admin user '{admin_user.username}' exists")
                return True
            else:
                self.log_test("Admin User", False, "No admin user found")
                return False
        except Exception as e:
            self.log_test("Admin User", False, f"Error: {str(e)}")
            return False
    
    def test_file_structure(self):
        """Test required files and directories exist"""
        required_files = [
            'manage.py',
            'detector.py',
            'requirements.txt',
            'face_security/settings.py',
            'faces/models.py',
            'faces/views.py',
            'faces/utils.py'
        ]
        
        required_dirs = [
            'media',
            'media/face_images',
            'media/detection_snapshots',
            'static',
            'faces/templates'
        ]
        
        missing_files = []
        missing_dirs = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
        
        if not missing_files and not missing_dirs:
            self.log_test("File Structure", True, "All required files and directories exist")
            return True
        else:
            missing = missing_files + missing_dirs
            self.log_test("File Structure", False, f"Missing: {', '.join(missing)}")
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        print("=" * 60)
        print("🔍 FACE DETECTION SYSTEM - COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Run all tests
        tests = [
            self.test_file_structure,
            self.test_database_connection,
            self.test_models,
            self.test_admin_user,
            self.test_face_recognition_imports,
            self.test_camera_access,
            self.test_email_configuration,
            self.test_utils_functions,
            self.test_django_server,
            self.test_api_endpoint
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Small delay for readability
        
        # Summary
        print("")
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['result'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("")
            print("🎉 ALL TESTS PASSED! System is ready for use.")
            print("")
            print("Next steps:")
            print("1. Start the system: python start_system.ps1")
            print("2. Open http://127.0.0.1:8000/ in your browser")
            print("3. Login with admin credentials")
            print("4. Register faces in the system")
            print("5. Run face detection: python detector.py")
        else:
            print("")
            print("⚠️  Some tests failed. Please review the errors above.")
            print("The system may still work with limited functionality.")
        
        return passed == total

def main():
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
