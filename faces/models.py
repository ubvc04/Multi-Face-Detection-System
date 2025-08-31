from django.db import models
import json
import logging

logger = logging.getLogger(__name__)

class Person(models.Model):
    """Model to store person information and their face data"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_face_count(self):
        """Return the number of face encodings for this person"""
        return self.faceencoding_set.count()

class FaceEncoding(models.Model):
    """Model to store face encodings for each person"""
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    encoding = models.JSONField(help_text="Face encoding stored as JSON array")
    image = models.ImageField(upload_to='face_images/', help_text="Original face image")
    created_at = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(default=1.0, help_text="Quality score of the face encoding")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.person.name} - Encoding {self.id}"
    
    def get_encoding_array(self):
        """Convert JSON encoding back to numpy array format"""
        try:
            if isinstance(self.encoding, str):
                return json.loads(self.encoding)
            return self.encoding
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error converting encoding for {self.person.name}: {e}")
            return None
    
    def set_encoding_array(self, encoding_array):
        """Convert numpy array to JSON for storage"""
        try:
            if hasattr(encoding_array, 'tolist'):
                self.encoding = encoding_array.tolist()
            else:
                self.encoding = list(encoding_array)
        except Exception as e:
            logger.error(f"Error setting encoding for {self.person.name}: {e}")
            raise

class DetectionLog(models.Model):
    """Model to log all face detection events"""
    DETECTION_TYPES = [
        ('recognized', 'Recognized'),
        ('unknown', 'Unknown'),
        ('multiple', 'Multiple Faces'),
        ('error', 'Detection Error'),
    ]
    
    person = models.ForeignKey(Person, null=True, blank=True, on_delete=models.SET_NULL)
    detection_type = models.CharField(max_length=20, choices=DETECTION_TYPES, default='unknown')
    confidence_score = models.FloatField(null=True, blank=True, help_text="Recognition confidence score")
    detection_time = models.DateTimeField(auto_now_add=True)
    image_snapshot = models.ImageField(upload_to='detection_snapshots/', null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the detection")
    email_sent = models.BooleanField(default=False, help_text="Whether email alert was sent")
    
    class Meta:
        ordering = ['-detection_time']
    
    def __str__(self):
        if self.person:
            return f"{self.person.name} - {self.detection_type} at {self.detection_time.strftime('%Y-%m-%d %H:%M:%S')}"
        return f"Unknown - {self.detection_type} at {self.detection_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def get_display_name(self):
        """Return display name for the detection"""
        if self.person and self.detection_type == 'recognized':
            return self.person.name
        elif self.detection_type == 'unknown':
            return "Unknown Person"
        elif self.detection_type == 'multiple':
            return "Multiple Faces"
        else:
            return "Detection Error"

class SystemSettings(models.Model):
    """Model to store system configuration settings"""
    setting_name = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"{self.setting_name}: {self.setting_value}"
    
    @classmethod
    def get_setting(cls, name, default=None):
        """Get a setting value by name"""
        try:
            setting = cls.objects.get(setting_name=name)
            return setting.setting_value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, name, value, description=""):
        """Set a setting value"""
        setting, created = cls.objects.get_or_create(
            setting_name=name,
            defaults={'setting_value': str(value), 'description': description}
        )
        if not created:
            setting.setting_value = str(value)
            setting.description = description
            setting.save()
        return setting
