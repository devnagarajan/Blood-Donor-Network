from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class DonorProfile(models.Model):
    """Donor Profile with detailed information"""
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    CONTACT_METHOD_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('both', 'Both'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    
    # Unique Donor ID - Auto-generated
    donor_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text='Auto-generated unique donor ID (format: DNR-YYYY-NNNNNN)'
    )
    
    # Personal Information
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    
    # Address Information
    address = models.TextField()
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Medical Information
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(45)],
        blank=True,
        null=True
    )
    last_donation_date = models.DateField(null=True, blank=True)
    medical_certificate = models.FileField(
        upload_to='donors/medical_certificates/',
        blank=True,
        null=True,
        help_text='Upload medical fitness certificate (PDF, JPG, PNG)'
    )
    
    # Availability
    is_available = models.BooleanField(default=True)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=CONTACT_METHOD_CHOICES,
        default='both'
    )
    
    # Eligibility
    medical_eligibility_confirmed = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    
    # Profile Status
    is_active = models.BooleanField(default=True)
    profile_completed = models.BooleanField(default=False)
    
    # Statistics
    total_donations = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'donor_profiles'
        verbose_name = 'Donor Profile'
        verbose_name_plural = 'Donor Profiles'
        indexes = [
            models.Index(fields=['blood_group', 'is_available', 'is_active']),
            models.Index(fields=['district', 'blood_group']),
        ]
    
    def __str__(self):
        return f"{self.donor_id} - {self.full_name} - {self.blood_group}"
    
    def save(self, *args, **kwargs):
        if not self.donor_id:
            # Generate unique donor ID: DNR-YYYY-NNNNNN
            from datetime import datetime
            year = datetime.now().year
            
            # Get last donor ID for this year
            last_donor = DonorProfile.objects.filter(
                donor_id__startswith=f'DNR-{year}-'
            ).order_by('-created_at').first()
            
            if last_donor:
                # Extract number and increment
                last_number = int(last_donor.donor_id.split('-')[-1])
                new_number = last_number + 1
            else:
                # First donor of the year
                new_number = 1
            
            # Format: DNR-2024-000001
            self.donor_id = f'DNR-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)
    
    def is_eligible_to_donate(self):
        """Check if donor is eligible to donate"""
        from datetime import date, timedelta
        
        if not self.last_donation_date:
            return True
        
        # Donors can donate every 3 months (90 days)
        eligible_date = self.last_donation_date + timedelta(days=90)
        return date.today() >= eligible_date
    
    def next_eligible_date(self):
        """Calculate next eligible donation date"""
        from datetime import timedelta
        
        if not self.last_donation_date:
            return None
        
        return self.last_donation_date + timedelta(days=90)
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class DonationHistory(models.Model):
    """Track donation history"""
    
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='donations'
    )
    donation_date = models.DateField()
    blood_group = models.CharField(max_length=3)
    units_donated = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    venue = models.CharField(max_length=255)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'donation_history'
        verbose_name = 'Donation History'
        verbose_name_plural = 'Donation Histories'
        ordering = ['-donation_date']
    
    def __str__(self):
        return f"{self.donor.full_name} - {self.donation_date}"
