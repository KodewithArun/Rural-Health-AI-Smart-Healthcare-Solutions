# from django.contrib import admin
from django.contrib import admin
from django import forms
from .models import ContactEnquiry
from .utils import send_response_to_user
from accounts.models import Account as User


class ContactEnquiryAdminForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter responded_by to show only users with admin role
        if 'responded_by' in self.fields:
            self.fields['responded_by'].queryset = User.objects.filter(role='admin')


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    form = ContactEnquiryAdminForm
    list_display = ('first_name', 'last_name', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'message')
    readonly_fields = ('user', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Enquiry Details', {
            'fields': ('message', 'status')
        }),
        ('Admin Response', {
            'fields': ('admin_response', 'responded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Save the responded_by field and send email when admin responds"""
        # Check if admin_response was added or changed
        if change and 'admin_response' in form.changed_data and obj.admin_response:
            obj.responded_by = request.user
            # Save first
            super().save_model(request, obj, form, change)
            # Then send email
            send_response_to_user(obj)
        else:
            if change and 'admin_response' in form.changed_data:
                obj.responded_by = request.user
            super().save_model(request, obj, form, change)
