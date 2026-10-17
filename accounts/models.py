from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    class Role(models.TextChoices):
        DONOR = 'DONOR', 'Donor'
        HOSPITAL = 'HOSPITAL', 'Hospital'
        NGO = 'NGO', 'NGO'
        ADMIN = 'ADMIN', 'Admin'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.DONOR
    )
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_donor(self):
        return self.role == self.Role.DONOR
    
    def is_hospital(self):
        return self.role == self.Role.HOSPITAL
    
    def is_ngo(self):
        return self.role == self.Role.NGO
