from django.contrib import admin
from .models import BloodRequest, DonorMatch, RequestStatusHistory

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'hospital', 'blood_group', 'units_required',
        'urgency', 'status', 'required_date', 'created_at'
    ]
    list_filter = [
        'blood_group', 'urgency', 'status', 'required_date', 'created_at'
    ]
    search_fields = [
        'request_id', 'hospital__hospital_name',
        'patient_name', 'contact_number'
    ]
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'accepted_at', 'fulfilled_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'hospital', 'status')
        }),
        ('Blood Requirements', {
            'fields': (
                'blood_group', 'units_required', 'units_fulfilled',
                'urgency', 'required_date'
            )
        }),
        ('Patient Information', {
            'fields': (
                'patient_name', 'patient_age', 'patient_gender', 'reason'
            )
        }),
        ('Contact', {
            'fields': ('contact_person', 'contact_number')
        }),
        ('NGO & Donors', {
            'fields': ('assigned_ngo',)
        }),
        ('Additional', {
            'fields': ('additional_notes',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at',
                'accepted_at', 'fulfilled_at'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(DonorMatch)
class DonorMatchAdmin(admin.ModelAdmin):
    list_display = [
        'blood_request', 'donor', 'match_status', 'notified_at'
    ]
    list_filter = ['match_status', 'notified_at']
    search_fields = [
        'blood_request__request_id',
        'donor__full_name'
    ]


@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'blood_request', 'old_status', 'new_status',
        'changed_by', 'created_at'
    ]
    list_filter = ['old_status', 'new_status', 'created_at']
    search_fields = ['blood_request__request_id']
    date_hierarchy = 'created_at'
