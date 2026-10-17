from django.urls import path
from . import views

app_name = 'donors'

urlpatterns = [
    # Authentication
    path('register/', views.donor_register, name='register'),
    path('login/', views.donor_login, name='login'),
    path('logout/', views.donor_logout, name='logout'),
    
    # Profile
    path('become-donor/', views.become_donor, name='become_donor'),
    path('dashboard/', views.donor_dashboard, name='dashboard'),
    path('profile/', views.donor_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Features
    path('donation-history/', views.donation_history, name='donation_history'),
    path('blood-requests/', views.blood_requests, name='blood_requests'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Donor Card View (Public - for QR code scanning)
    path('card/<int:donor_id>/', views.donor_card_view, name='donor_card_view'),
]
