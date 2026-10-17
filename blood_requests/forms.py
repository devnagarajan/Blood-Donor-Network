from django import forms
from .models import DonationConfirmation, BloodRequest
from donors.models import DonorProfile


class DonationConfirmationForm(forms.ModelForm):
    """Form for Hospital Staff to Confirm Donation"""
    
    BLOOD_GROUP_CHOICES = BloodRequest.BLOOD_GROUP_CHOICES
    
    blood_group = forms.ChoiceField(
        choices=BloodRequest.BLOOD_GROUP_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Blood Group *'
    )
    
    donation_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Donation Date *'
    )
    
    donation_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Donation Time *'
    )
    
    units_donated = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        initial=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.5',
            'min': '0.5',
            'max': '2.0'
        }),
        label='Units Donated *',
        help_text='1 unit = 450ml (usually 1.0)'
    )
    
    blood_bag_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., BB-2024-001234'
        }),
        label='Blood Bag ID *',
        help_text='Unique blood bag / donation reference ID'
    )
    
    staff_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Staff member name'
        }),
        label='Staff Name *'
    )
    
    staff_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional staff ID'
        }),
        label='Staff ID (Optional)'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes or observations'
        }),
        label='Notes (Optional)'
    )
    
    class Meta:
        model = DonationConfirmation
        fields = ['donor', 'blood_group', 'units_donated', 'blood_bag_id', 
                  'staff_name', 'staff_id', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom attributes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class OTPVerificationForm(forms.Form):
    """Form for Donor OTP Verification"""
    
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'style': 'letter-spacing: 1rem; font-size: 2rem; font-weight: bold;'
        }),
        label='Enter 6-Digit OTP',
        help_text='OTP has been sent to your registered mobile number'
    )
    
    def clean_otp_code(self):
        otp = self.cleaned_data.get('otp_code')
        if not otp.isdigit():
            raise forms.ValidationError('OTP must contain only numbers.')
        return otp
