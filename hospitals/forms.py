from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import HospitalProfile
from blood_requests.models import BloodRequest
import re

class HospitalRegistrationForm(UserCreationForm):
    """Hospital Registration Form"""
    
    # Account Details
    hospital_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital Name'})
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
        user.role = User.Role.HOSPITAL
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user


class HospitalProfileForm(forms.ModelForm):
    """Hospital Profile Form"""
    
    class Meta:
        model = HospitalProfile
        exclude = [
            'user', 'verification_status', 'is_active',
            'total_requests', 'fulfilled_requests',
            'created_at', 'updated_at', 'verified_at'
        ]
        widgets = {
            'hospital_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '22AAAAA0000A1Z5'}),
            'hospital_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'registration_document': forms.FileInput(attrs={'class': 'form-control'}),
            'gst_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number')
        if gst:
            # GST format: 22AAAAA0000A1Z5
            pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
            if not re.match(pattern, gst):
                raise forms.ValidationError('Invalid GST Number format. Example: 22AAAAA0000A1Z5')
        return gst


class BloodRequestForm(forms.ModelForm):
    """Simple Blood Request Form - Blood Group + Units + Required Date"""
    
    class Meta:
        model = BloodRequest
        fields = ['blood_group', 'units_required', 'required_date']
        widgets = {
            'blood_group': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'required': True
            }),
            'units_required': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '1',
                'min': '1',
                'placeholder': 'Enter number of units'
            }),
            'required_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'required': True
            }),
        }
