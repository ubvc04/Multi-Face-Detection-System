from django.contrib import admin
from django.utils.html import format_html
from .models import Person, FaceEncoding, DetectionLog, SystemSettings

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_face_count', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_face_count(self, obj):
        return obj.get_face_count()
    get_face_count.short_description = 'Face Images'

@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('person', 'image_thumbnail', 'confidence_score', 'created_at')
    list_filter = ('created_at', 'person')
    search_fields = ('person__name',)
    readonly_fields = ('created_at', 'image_thumbnail')
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_thumbnail.short_description = 'Thumbnail'

@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    list_display = ('get_display_name', 'detection_type', 'confidence_score', 'detection_time', 'email_sent', 'image_thumbnail')
    list_filter = ('detection_type', 'email_sent', 'detection_time', 'person')
    search_fields = ('person__name', 'notes')
    readonly_fields = ('detection_time', 'image_thumbnail')
    date_hierarchy = 'detection_time'
    
    def image_thumbnail(self, obj):
        if obj.image_snapshot:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image_snapshot.url)
        return "No Image"
    image_thumbnail.short_description = 'Snapshot'

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_name', 'setting_value', 'description', 'updated_at')
    search_fields = ('setting_name', 'description')
    readonly_fields = ('updated_at',)
