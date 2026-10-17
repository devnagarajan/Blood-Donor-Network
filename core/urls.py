from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Public Pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('blood-camps/', views.blood_camps_public, name='blood_camps_public'),
    
    # Article Pages
    path('articles/save-lives/', views.article_save_lives, name='article_save_lives'),
    path('articles/health-benefits/', views.article_health_benefits, name='article_health_benefits'),
    path('articles/community-service/', views.article_community_service, name='article_community_service'),
    path('articles/quick-process/', views.article_quick_process, name='article_quick_process'),
    
    # Login Redirect
    path('login/', views.login_redirect, name='login_redirect'),
]
