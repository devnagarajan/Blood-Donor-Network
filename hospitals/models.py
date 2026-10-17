from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class HospitalProfile(models.Model):
    """Hospital Profile"""
    
    HOSPITAL_TYPE_CHOICES = [
        ('government', 'Government'),
        ('private', 'Private'),
        ('trust', 'Trust'),
        ('charitable', 'Charitable'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    
    # Hospital Details
    hospital_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    
    # Registration Details
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Hospital Registration Number'
    )
    
    gst_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$',
                message='Invalid GST Number format. Example: 22AAAAA0000A1Z5'
            )
        ],
        help_text='GST Number (15 characters)'
    )
    
    hospital_type = models.CharField(
        max_length=20,
        choices=HOSPITAL_TYPE_CHOICES
    )
    
    # Address
    address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Contact Person (Optional)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_designation = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Additional Information
    website = models.URLField(blank=True, null=True)
    
    # Documents
    registration_document = models.FileField(
        upload_to='hospitals/documents/',
        blank=True,
        null=True
    )
    gst_document = models.FileField(
        upload_to='hospitals/documents/',
        blank=True,
        null=True
    )
    
    # Status
    verification_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics
    total_requests = models.IntegerField(default=0)
    fulfilled_requests = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'hospital_profiles'
        verbose_name = 'Hospital Profile'
        verbose_name_plural = 'Hospital Profiles'
    
    def __str__(self):
        return self.hospital_name
    
    def is_verified(self):
        return self.verification_status == 'verified'
