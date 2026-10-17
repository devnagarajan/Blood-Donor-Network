from django.urls import path
from . import views

app_name = 'camps'

urlpatterns = [
    path('', views.camps_list, name='camps_list'),
    path('<int:pk>/', views.camp_detail, name='camp_detail'),
    path('<int:pk>/register/', views.register_for_camp, name='register'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
]
