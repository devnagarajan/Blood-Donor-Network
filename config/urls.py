"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect

# Favicon view to prevent 404 errors
def favicon_view(request):
    """Return empty response for favicon requests"""
    return HttpResponse(status=204)  # No Content

# Custom admin logout view
def admin_logout_view(request):
    """Logout admin user and redirect to home"""
    logout(request)
    return redirect('core:home')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-logout/', admin_logout_view, name='admin_logout'),
    path('favicon.ico', favicon_view, name='favicon'),  # Handle favicon requests
    path('', include('core.urls')),
    path('donor/', include('donors.urls')),
    path('hospital/', include('hospitals.urls')),
    path('ngo/', include('ngos.urls')),
    path('camps/', include('camps.urls')),
    
    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
