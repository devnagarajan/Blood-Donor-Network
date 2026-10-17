from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import NGOProfile
from camps.models import BloodCamp
import re

class NGORegistrationForm(UserCreationForm):
    """NGO Registration Form"""
    
    # Account Details
    ngo_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NGO Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.NGO
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user


class NGOProfileForm(forms.ModelForm):
    """NGO Profile Form"""
    
    class Meta:
        model = NGOProfile
        exclude = [
            'user', 'verification_status', 'is_active',
            'total_requests_handled', 'completed_requests', 'total_camps_organized',
            'created_at', 'updated_at', 'verified_at'
        ]
        widgets = {
            'ngo_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22AAAAA0000A1Z5'}),
            'ngo_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'registration_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'gst_document': forms.FileInput(attrs={'class': 'form-control'}),
            'other_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number')
        if gst:
            # GST format: 22AAAAA0000A1Z5
            pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
            if not re.match(pattern, gst):
                raise forms.ValidationError('Invalid GST Number format. Example: 22AAAAA0000A1Z5')
        return gst


class BloodCampForm(forms.ModelForm):
    """Blood Camp Creation Form"""
    
    class Meta:
        model = BloodCamp
        exclude = ['organized_by', 'registered_count', 'actual_donors', 'units_collected', 'created_at', 'updated_at']
        widgets = {
            'camp_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'camp_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'venue_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'total_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_registration_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
