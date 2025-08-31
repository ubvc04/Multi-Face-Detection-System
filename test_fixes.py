#!/usr/bin/env python
"""
Test script to verify all implemented fixes
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_security.settings')
django.setup()

from faces.models import Person, FaceEncoding, SystemSettings, DetectionLog
from faces.utils import check_face_duplicate, compare_faces
import numpy as np

def test_system_settings():
    """Test if system settings are properly configured"""
    print("🧪 Testing System Settings...")
    
    recognition_threshold = SystemSettings.get_setting('recognition_threshold', None)
    duplicate_threshold = SystemSettings.get_setting('duplicate_threshold', None)
    email_alerts = SystemSettings.get_setting('email_alerts', None)
    alert_cooldown = SystemSettings.get_setting('alert_cooldown', None)
    
    if not all([recognition_threshold, duplicate_threshold, email_alerts, alert_cooldown]):
        print("❌ Some system settings are missing")
        return False
    
    print(f"✅ Recognition threshold: {recognition_threshold}")
    print(f"✅ Duplicate threshold: {duplicate_threshold}")
    print(f"✅ Email alerts: {email_alerts}")
    print(f"✅ Alert cooldown: {alert_cooldown}")
    return True

def test_models():
    """Test if models are working correctly"""
    print("\n🧪 Testing Database Models...")
    
    try:
        # Test Person model
        person_count = Person.objects.count()
        print(f"✅ Person model: {person_count} persons in database")
        
        # Test FaceEncoding model
        encoding_count = FaceEncoding.objects.count()
        print(f"✅ FaceEncoding model: {encoding_count} encodings in database")
        
        # Test DetectionLog model
        log_count = DetectionLog.objects.count()
        print(f"✅ DetectionLog model: {log_count} logs in database")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_face_comparison():
    """Test the enhanced face comparison function"""
    print("\n🧪 Testing Enhanced Face Comparison...")
    
    try:
        # Create two random face encodings for testing
        encoding1 = np.random.rand(128)
        encoding2 = np.random.rand(128)
        encoding3 = encoding1 + np.random.rand(128) * 0.1  # Similar to encoding1
        
        # Test comparison with different tolerance levels
        is_match1, idx1, conf1 = compare_faces([encoding1], encoding2, tolerance=0.6)
        is_match2, idx2, conf2 = compare_faces([encoding1], encoding3, tolerance=0.6)
        
        print(f"✅ Random encodings match: {is_match1} (confidence: {conf1:.3f})")
        print(f"✅ Similar encodings match: {is_match2} (confidence: {conf2:.3f})")
        
        return True
    except Exception as e:
        print(f"❌ Face comparison test failed: {e}")
        return False

def test_duplicate_detection():
    """Test duplicate face detection"""
    print("\n🧪 Testing Duplicate Face Detection...")
    
    try:
        # Test with random encoding
        test_encoding = np.random.rand(128)
        is_duplicate, person_name, confidence = check_face_duplicate(test_encoding)
        
        print(f"✅ Duplicate detection working: duplicate={is_duplicate}, person={person_name}, confidence={confidence:.3f}")
        return True
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
        return False

def test_import_dependencies():
    """Test if all required dependencies are available"""
    print("\n🧪 Testing Import Dependencies...")
    
    try:
        import face_recognition
        print("✅ face_recognition library imported successfully")
        
        import cv2
        print("✅ OpenCV library imported successfully")
        
        import numpy as np
        print("✅ NumPy library imported successfully")
        
        import django
        print("✅ Django framework imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\n🧪 Testing File Structure...")
    
    required_files = [
        'faces/models.py',
        'faces/views.py',
        'faces/utils.py',
        'enhanced_detector.py',
        'faces/templates/faces/register_face.html',
        'faces/templates/faces/system_settings.html',
        'faces/templates/faces/detection_logs.html',
        'manage.py',
        'update_settings.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 Face Detection System - Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        ("Import Dependencies", test_import_dependencies),
        ("File Structure", test_file_structure),
        ("Database Models", test_models),
        ("System Settings", test_system_settings),
        ("Face Comparison", test_face_comparison),
        ("Duplicate Detection", test_duplicate_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for use.")
        print("\n🚀 Next Steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Start detection system: python enhanced_detector.py")
        print("3. Open browser: http://127.0.0.1:8000/")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
