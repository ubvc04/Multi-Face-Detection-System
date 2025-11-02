from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('api/check-username/', views.check_username_availability, name='check_username'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Person management
    path('persons/', views.person_list, name='person_list'),
    path('persons/<int:person_id>/', views.person_detail, name='person_detail'),
    path('persons/<int:person_id>/delete/', views.delete_person, name='delete_person'),
    
    # Face registration
    path('register/', views.register_face, name='register_face'),
    path('encodings/<int:encoding_id>/delete/', views.delete_face_encoding, name='delete_face_encoding'),
    
    # Detection logs
    path('logs/', views.detection_logs, name='detection_logs'),
    
    # System settings
    path('settings/', views.system_settings, name='system_settings'),
    
    # Camera streaming
    path('camera/feed/', views.camera_feed, name='camera_feed'),
    path('camera/control/', views.camera_control, name='camera_control'),
    path('camera/status/', views.camera_status, name='camera_status'),
    path('camera/unknown-faces/', views.get_unknown_faces, name='get_unknown_faces'),
    
    # API endpoint for detection script
    path('api/detection/', views.detection_api, name='detection_api'),
]
