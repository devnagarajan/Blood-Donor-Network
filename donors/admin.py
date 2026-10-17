from django.contrib import admin
from .models import DonorProfile, DonationHistory

@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'blood_group', 'district', 'is_available',
        'is_active', 'profile_completed', 'total_donations'
    ]
    list_filter = [
        'blood_group', 'is_available', 'is_active',
        'profile_completed', 'state', 'district'
    ]
    search_fields = ['full_name', 'email', 'phone_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'date_of_birth', 'gender', 'blood_group')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'preferred_contact_method')
        }),
        ('Address', {
            'fields': ('address', 'state', 'district', 'city', 'pincode')
        }),
        ('Medical Information', {
            'fields': ('last_donation_date', 'medical_certificate', 'medical_eligibility_confirmed')
        }),
        ('Availability', {
            'fields': ('is_available', 'terms_accepted')
        }),
        ('Status', {
            'fields': ('is_active', 'profile_completed', 'total_donations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DonationHistory)
class DonationHistoryAdmin(admin.ModelAdmin):
    list_display = ['donor', 'donation_date', 'blood_group', 'units_donated', 'venue']
    list_filter = ['donation_date', 'blood_group']
    search_fields = ['donor__full_name', 'venue']
    date_hierarchy = 'donation_date'
