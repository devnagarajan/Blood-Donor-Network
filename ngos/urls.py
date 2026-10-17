from django.urls import path
from . import views

app_name = 'ngos'

urlpatterns = [
    # Authentication
    path('register/', views.ngo_register, name='register'),
    path('login/', views.ngo_login, name='login'),
    path('logout/', views.ngo_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.ngo_dashboard, name='dashboard'),
    path('profile/', views.ngo_profile, name='profile'),
    path('profile/edit/', views.edit_ngo_profile, name='edit_profile'),
    
    # Blood Requests Management
    path('blood-requests/', views.blood_requests_list, name='blood_requests_list'),
    path('blood-request/<int:pk>/', views.blood_request_detail, name='blood_request_detail'),
    path('blood-request/<int:pk>/accept/', views.accept_request, name='accept_request'),
    path('blood-request/<int:pk>/update-status/', views.update_request_status, name='update_request_status'),
    path('blood-requests/export-csv/', views.export_blood_requests_csv, name='export_blood_requests_csv'),
    path('blood-requests/export-pdf/', views.export_blood_requests_pdf, name='export_blood_requests_pdf'),
    
    # Donor Management
    path('donors/', views.donor_management, name='donor_management'),
    path('donor/<int:pk>/', views.donor_detail, name='donor_detail'),
    path('donors/export-csv/', views.export_donors_csv, name='export_donors_csv'),
    path('donors/export-pdf/', views.export_donors_pdf, name='export_donors_pdf'),
    path('donor/<int:pk>/download-receipt/', views.download_donor_receipt, name='download_donor_receipt'),
    
    # Blood Camps
    path('camps/', views.camps_list, name='camps_list'),
    path('camp/create/', views.create_camp, name='create_camp'),
    path('camp/<int:pk>/', views.camp_detail, name='camp_detail'),
    path('camp/<int:pk>/edit/', views.edit_camp, name='edit_camp'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
]
