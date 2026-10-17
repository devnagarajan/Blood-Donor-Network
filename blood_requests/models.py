from django.db import models
from django.conf import settings
from hospitals.models import HospitalProfile
from donors.models import DonorProfile
from ngos.models import NGOProfile
import datetime

class BloodRequest(models.Model):
    """Blood Request from Hospital"""
    
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
    
    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    PATIENT_GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Request ID
    request_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Hospital
    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    
    # Blood Details
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units_required = models.DecimalField(max_digits=5, decimal_places=2)
    units_fulfilled = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES)
    required_date = models.DateField()
    
    # Patient Details
    patient_name = models.CharField(max_length=255)
    patient_age = models.IntegerField()
    patient_gender = models.CharField(max_length=1, choices=PATIENT_GENDER_CHOICES)
    reason = models.TextField(help_text='Medical requirement/reason')
    
    # Hospital Contact (from profile, stored for reference)
    contact_person = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=15)
    
    # Additional Information
    additional_notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # NGO Assignment
    assigned_ngo = models.ForeignKey(
        NGOProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    
    # Matched Donors
    matched_donors = models.ManyToManyField(
        DonorProfile,
        through='DonorMatch',
        related_name='matched_requests'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'blood_requests'
        verbose_name = 'Blood Request'
        verbose_name_plural = 'Blood Requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blood_group', 'status']),
            models.Index(fields=['hospital', 'status']),
        ]
    
    def __str__(self):
        return f"{self.request_id} - {self.blood_group} - {self.hospital.hospital_name}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            # Generate unique request ID: BR-YYYY-NNNNNN
            year = datetime.datetime.now().year
            last_request = BloodRequest.objects.filter(
                request_id__startswith=f'BR-{year}-'
            ).order_by('-created_at').first()
            
            if last_request:
                last_number = int(last_request.request_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.request_id = f'BR-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)
    
    def is_urgent(self):
        return self.urgency in ['urgent', 'emergency']
    
    def remaining_units(self):
        return self.units_required - self.units_fulfilled


class DonorMatch(models.Model):
    """Many-to-Many relationship between Blood Request and Donors"""
    
    MATCH_STATUS_CHOICES = [
        ('notified', 'Notified'),
        ('contacted', 'Contacted'),
        ('agreed', 'Agreed'),
        ('donated', 'Donated'),
        ('declined', 'Declined'),
        ('unavailable', 'Unavailable'),
    ]
    
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE
    )
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE
    )
    match_status = models.CharField(
        max_length=15,
        choices=MATCH_STATUS_CHOICES,
        default='notified'
    )
    notified_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'donor_matches'
        unique_together = ['blood_request', 'donor']
    
    def __str__(self):
        return f"{self.blood_request.request_id} - {self.donor.full_name}"


class RequestStatusHistory(models.Model):
    """Track status changes of blood requests"""
    
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'request_status_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.blood_request.request_id} - {self.old_status} to {self.new_status}"



class DonationConfirmation(models.Model):
    """Hospital Staff Confirmed Donations"""
    
    STATUS_CHOICES = [
        ('pending_otp', 'Pending OTP Verification'),
        ('verified', 'Verified'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Donation ID - Auto-generated
    donation_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # References
    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name='confirmed_donations'
    )
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='confirmed_donations'
    )
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_donations',
        help_text='Optional: Link to blood request if applicable'
    )
    
    # Donation Details
    blood_group = models.CharField(max_length=3, choices=BloodRequest.BLOOD_GROUP_CHOICES)
    donation_datetime = models.DateTimeField()
    units_donated = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=1.0,
        help_text='Units of blood donated (usually 1 unit = 450ml)'
    )
    
    # Blood Bag Details
    blood_bag_id = models.CharField(
        max_length=50,
        unique=True,
        help_text='Blood bag / donation reference ID'
    )
    
    # Staff Details
    staff_name = models.CharField(max_length=255)
    staff_id = models.CharField(max_length=50, blank=True, null=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='confirmed_donations'
    )
    
    # OTP Verification
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_sent_at = models.DateTimeField(null=True, blank=True)
    otp_verified_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_otp'
    )
    
    # Additional Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'donation_confirmations'
        verbose_name = 'Donation Confirmation'
        verbose_name_plural = 'Donation Confirmations'
        ordering = ['-donation_datetime']
        indexes = [
            models.Index(fields=['hospital', 'status']),
            models.Index(fields=['donor', 'status']),
            models.Index(fields=['donation_datetime']),
        ]
    
    def __str__(self):
        return f"{self.donation_id} - {self.donor.full_name} - {self.blood_group}"
    
    def save(self, *args, **kwargs):
        if not self.donation_id:
            # Generate unique donation ID: DN-YYYY-NNNNNN
            year = datetime.datetime.now().year
            last_donation = DonationConfirmation.objects.filter(
                donation_id__startswith=f'DN-{year}-'
            ).order_by('-created_at').first()
            
            if last_donation:
                last_number = int(last_donation.donation_id.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.donation_id = f'DN-{year}-{new_number:06d}'
        
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        """Generate 6-digit OTP"""
        import random
        self.otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_sent_at = datetime.datetime.now()
        self.save()
        return self.otp_code
    
    def verify_otp(self, entered_otp):
        """Verify OTP"""
        from django.utils import timezone
        
        # Check if OTP expired (valid for 10 minutes)
        if self.otp_sent_at:
            time_diff = timezone.now() - self.otp_sent_at
            if time_diff.total_seconds() > 600:  # 10 minutes
                return False, "OTP expired. Please request a new one."
        
        # Check attempts
        if self.otp_attempts >= 3:
            return False, "Maximum OTP attempts exceeded."
        
        # Verify OTP
        if self.otp_code == entered_otp:
            self.status = 'verified'
            self.otp_verified_at = timezone.now()
            self.save()
            return True, "OTP verified successfully!"
        else:
            self.otp_attempts += 1
            self.save()
            return False, f"Invalid OTP. {3 - self.otp_attempts} attempts remaining."
