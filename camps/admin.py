from django.contrib import admin
from .models import BloodCamp, CampRegistration

@admin.register(BloodCamp)
class BloodCampAdmin(admin.ModelAdmin):
    list_display = [
        'camp_name', 'organized_by', 'camp_date',
        'venue_name', 'district', 'total_capacity',
        'registered_count', 'status'
    ]
    list_filter = [
        'status', 'camp_date', 'state', 'district',
        'is_registration_open'
    ]
    search_fields = [
        'camp_name', 'venue_name', 'organized_by__ngo_name',
        'contact_person'
    ]
    date_hierarchy = 'camp_date'
    readonly_fields = ['registered_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Camp Basic Details', {
            'fields': ('camp_name', 'description', 'organized_by')
        }),
        ('Date & Time Schedule', {
            'fields': ('camp_date', 'start_time', 'end_time')
        }),
        ('Venue Details', {
            'fields': (
                'venue_name', 'address', 'district',
                'state', 'pincode'
            )
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_number')
        }),
        ('Capacity & Registration', {
            'fields': (
                'total_capacity', 'registered_count',
                'is_registration_open', 'status'
            )
        }),
        ('Banner Image', {
            'fields': ('banner_image',),
            'classes': ('collapse',)
        }),
        ('System Fields (Read Only)', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CampRegistration)
class CampRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'camp', 'donor', 'status', 'registration_date'
    ]
    list_filter = ['status', 'registration_date', 'camp__camp_date']
    search_fields = [
        'camp__camp_name', 'donor__full_name'
    ]
    date_hierarchy = 'registration_date'
