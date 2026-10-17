from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_display_role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'email')}),
    )
    
    def get_display_role(self, obj):
        """Display proper role - show Admin for staff/superuser"""
        if obj.is_superuser or obj.is_staff:
            return 'Admin'
        return obj.get_role_display()
    get_display_role.short_description = 'Role'
    get_display_role.admin_order_field = 'role'
    
    def get_queryset(self, request):
        """Override to show all users including admins"""
        qs = super().get_queryset(request)
        return qs
    
    def save_model(self, request, obj, form, change):
        """Auto-set role to ADMIN for staff/superuser"""
        if obj.is_superuser or obj.is_staff:
            obj.role = User.Role.ADMIN
        super().save_model(request, obj, form, change)
