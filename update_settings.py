#!/usr/bin/env python
"""
Script to update system settings with improved defaults
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_security.settings')
django.setup()

from faces.models import SystemSettings

def update_system_settings():
    """Update system settings with new defaults"""
    try:
        # Set improved recognition threshold
        SystemSettings.set_setting(
            'recognition_threshold', 
            '0.45', 
            'Face recognition confidence threshold (lower = more strict, prevents sibling mixups)'
        )
        
        # Set duplicate detection threshold
        SystemSettings.set_setting(
            'duplicate_threshold', 
            '0.4', 
            'Threshold for detecting duplicate faces during registration'
        )
        
        # Set email alerts (enabled by default)
        SystemSettings.set_setting(
            'email_alerts', 
            'True', 
            'Enable/disable email alerts for unknown face detection'
        )
        
        # Set alert cooldown
        SystemSettings.set_setting(
            'alert_cooldown', 
            '300', 
            'Cooldown period between alerts (seconds) - default 5 minutes'
        )
        
        print("✅ System settings updated successfully!")
        print(f"📊 Recognition threshold: 0.45 (strict - prevents sibling mixups)")
        print(f"🔍 Duplicate threshold: 0.4 (prevents duplicate registrations)")
        print(f"📧 Email alerts: Enabled")
        print(f"⏰ Alert cooldown: 300 seconds (5 minutes)")
        
        # Display current settings
        print("\n🔧 Current System Settings:")
        for setting in SystemSettings.objects.all():
            print(f"   {setting.setting_name}: {setting.setting_value}")
            if setting.description:
                print(f"      └─ {setting.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Updating Face Detection System Settings...")
    print("=" * 50)
    
    success = update_system_settings()
    
    if success:
        print("\n✨ Settings update completed successfully!")
        print("🔄 Please restart the detection system for changes to take effect.")
    else:
        print("\n❌ Settings update failed!")
        sys.exit(1)
