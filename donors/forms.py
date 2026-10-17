from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import User
from .models import DonorProfile

class DonorRegistrationForm(UserCreationForm):
    """Donor Registration Form"""
    
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
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
        fields = ['username', 'full_name', 'email', 'phone_number', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DONOR
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.first_name = self.cleaned_data['full_name']
        if commit:
            user.save()
        return user


class DonorProfileForm(forms.ModelForm):
    """Donor Profile Form"""
    
    class Meta:
        model = DonorProfile
        exclude = ['user', 'profile_completed', 'total_donations', 'created_at', 'updated_at', 
                   'emergency_contact_name', 'emergency_contact_number', 'weight']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'last_donation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preferred_contact_method': forms.Select(attrs={'class': 'form-control'}),
            'medical_eligibility_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'terms_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        medical_confirmed = cleaned_data.get('medical_eligibility_confirmed')
        terms_accepted = cleaned_data.get('terms_accepted')
        
        if not medical_confirmed:
            raise forms.ValidationError('You must confirm your medical eligibility.')
        
        if not terms_accepted:
            raise forms.ValidationError('You must accept the terms and conditions.')
        
        return cleaned_data
