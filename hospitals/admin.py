from django.contrib import admin
from .models import HospitalProfile

@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = [
        'hospital_name', 'district', 'hospital_type',
        'verification_status', 'is_active', 'total_requests'
    ]
    list_filter = [
        'hospital_type', 'verification_status', 'is_active', 'state', 'district'
    ]
    search_fields = [
        'hospital_name', 'email',
        'gst_number', 'user__username'
    ]
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Hospital Details', {
            'fields': (
                'hospital_name', 'email', 'phone_number',
                'hospital_type', 'gst_number'
            )
        }),
        ('Address', {
            'fields': ('address', 'state', 'district', 'city', 'pincode')
        }),
        ('Documents', {
            'fields': ('gst_document',)
        }),
        ('Status', {
            'fields': (
                'verification_status', 'is_active',
                'total_requests', 'fulfilled_requests'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_hospitals', 'reject_hospitals']
    
    def verify_hospitals(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='verified',
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} hospitals verified successfully.')
    verify_hospitals.short_description = 'Verify selected hospitals'
    
    def reject_hospitals(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} hospitals rejected.')
    reject_hospitals.short_description = 'Reject selected hospitals'
