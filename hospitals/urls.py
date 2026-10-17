from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    # Authentication
    path('register/', views.hospital_register, name='register'),
    path('login/', views.hospital_login, name='login'),
    path('logout/', views.hospital_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
    path('profile/', views.hospital_profile, name='profile'),
    path('profile/edit/', views.edit_hospital_profile, name='edit_profile'),
    
    # Blood Requests
    path('blood-request/create/', views.create_blood_request, name='create_blood_request'),
    path('blood-request/emergency/', views.create_emergency_request, name='create_emergency_request'),
    path('blood-requests/', views.blood_requests_list, name='blood_requests_list'),
    path('blood-request/<int:pk>/', views.blood_request_detail, name='blood_request_detail'),
    path('blood-request/<int:pk>/cancel/', views.cancel_blood_request, name='cancel_blood_request'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # Donation Confirmation (Hospital Staff - Direct Confirmation)
    path('confirm-donation/', views.confirm_donation, name='confirm_donation'),
    path('donation-success/<int:pk>/', views.donation_success, name='donation_success'),
    path('donation-confirmations/', views.donation_confirmations_list, name='donation_confirmations_list'),
    path('donation-confirmation/<int:pk>/', views.donation_confirmation_detail, name='donation_confirmation_detail'),
    
    # Export Donation Confirmations
    path('donation-confirmations/export-csv/', views.export_confirmations_csv, name='export_confirmations_csv'),
    path('donation-confirmations/export-pdf/', views.export_confirmations_pdf, name='export_confirmations_pdf'),
    path('donation-confirmation/<int:pk>/download-receipt/', views.download_donation_receipt, name='download_donation_receipt'),
    
    # API - Get Donor Details by Donor ID
    path('api/donor/<str:donor_id>/', views.get_donor_details_api, name='get_donor_details_api'),
]
