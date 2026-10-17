from django.contrib import admin
from .models import NGOProfile

@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = [
        'ngo_name', 'district', 'ngo_type',
        'verification_status', 'is_active', 'total_requests_handled'
    ]
    list_filter = [
        'ngo_type', 'verification_status', 'is_active', 'state', 'district'
    ]
    search_fields = [
        'ngo_name', 'email',
        'gst_number', 'user__username'
    ]
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('NGO Details', {
            'fields': ('ngo_name', 'email', 'phone_number', 'ngo_type', 'gst_number')
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
                'total_requests_handled', 'completed_requests',
                'total_camps_organized'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_ngos', 'reject_ngos']
    
    def verify_ngos(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='verified',
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} NGOs verified successfully.')
    verify_ngos.short_description = 'Verify selected NGOs'
    
    def reject_ngos(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} NGOs rejected.')
    reject_ngos.short_description = 'Reject selected NGOs'
