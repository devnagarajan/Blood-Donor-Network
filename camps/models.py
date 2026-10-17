from django.db import models
from django.conf import settings
from ngos.models import NGOProfile
from donors.models import DonorProfile

class BloodCamp(models.Model):
    """Blood Donation Camps"""
    
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Camp Details
    camp_name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Organization
    organized_by = models.ForeignKey(
        NGOProfile,
        on_delete=models.CASCADE,
        related_name='organized_camps'
    )
    
    # Date and Time
    camp_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Venue
    venue_name = models.CharField(max_length=255)
    address = models.TextField()
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Contact
    contact_number = models.CharField(max_length=15)
    contact_person = models.CharField(max_length=255, blank=True)
    
    # Capacity
    total_capacity = models.IntegerField(
        help_text='Total number of donors that can be accommodated'
    )
    registered_count = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='upcoming'
    )
    is_registration_open = models.BooleanField(default=True)
    
    # Image
    banner_image = models.ImageField(
        upload_to='camps/banners/',
        blank=True,
        null=True
    )
    
    # Statistics
    actual_donors = models.IntegerField(default=0, help_text='Actual number of donors who donated')
    units_collected = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blood_camps'
        verbose_name = 'Blood Camp'
        verbose_name_plural = 'Blood Camps'
        ordering = ['camp_date', 'start_time']
    
    def __str__(self):
        return f"{self.camp_name} - {self.camp_date}"
    
    def available_seats(self):
        return self.total_capacity - self.registered_count
    
    def is_full(self):
        return self.registered_count >= self.total_capacity
    
    def can_register(self):
        return (
            self.is_registration_open and
            not self.is_full() and
            self.status == 'upcoming'
        )


class CampRegistration(models.Model):
    """Donor registration for blood camps"""
    
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('donated', 'Donated'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    camp = models.ForeignKey(
        BloodCamp,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='camp_registrations'
    )
    
    # Registration Details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='registered'
    )
    
    # Additional Information
    remarks = models.TextField(blank=True)
    units_donated = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text='Units donated at camp'
    )
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'camp_registrations'
        unique_together = ['camp', 'donor']
        verbose_name = 'Camp Registration'
        verbose_name_plural = 'Camp Registrations'
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.donor.full_name} - {self.camp.camp_name}"
