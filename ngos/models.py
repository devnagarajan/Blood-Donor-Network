from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class NGOProfile(models.Model):
    """NGO Profile"""
    
    NGO_TYPE_CHOICES = [
        ('blood_bank', 'Blood Bank'),
        ('social_welfare', 'Social Welfare'),
        ('health', 'Health Organization'),
        ('charitable', 'Charitable Trust'),
        ('other', 'Other'),
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
        related_name='ngo_profile'
    )
    
    # NGO Details
    ngo_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    
    # Registration Details
    registration_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text='NGO Registration Number'
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
    
    ngo_type = models.CharField(
        max_length=20,
        choices=NGO_TYPE_CHOICES
    )
    
    # Address
    address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Contact Person
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_designation = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Additional Information
    website = models.URLField(blank=True, null=True)
    
    # Documents
    registration_certificate = models.FileField(
        upload_to='ngos/documents/',
        blank=True,
        null=True
    )
    gst_document = models.FileField(
        upload_to='ngos/documents/',
        blank=True,
        null=True
    )
    other_document = models.FileField(
        upload_to='ngos/documents/',
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
    total_requests_handled = models.IntegerField(default=0)
    completed_requests = models.IntegerField(default=0)
    total_camps_organized = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ngo_profiles'
        verbose_name = 'NGO Profile'
        verbose_name_plural = 'NGO Profiles'
    
    def __str__(self):
        return self.ngo_name
    
    def is_verified(self):
        return self.verification_status == 'verified'
