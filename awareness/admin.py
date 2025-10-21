# from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings
from .models import Awareness

@admin.register(Awareness)
class AwarenessAdmin(ModelAdmin):
    list_display = ('title', 'get_date_display', 'created_at', 'is_event')
    list_filter = ('is_event', 'event_date')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_event')
        }),
        ('Media', {
            'fields': ('photo', 'pdf')
        }),
        ('Event Details', {
            'fields': ('event_date',),
            'classes': ('collapse',),
            'description': 'Only fill this in if this is an event with a specific date'
        }),
    )
    
    def get_date_display(self, obj):
        if obj.event_date:
            return obj.event_date
        return "N/A (Informational)"
    get_date_display.short_description = 'Date'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only send email on creation
            self.send_awareness_email(obj)
    
    def send_awareness_email(self, awareness):
        User = get_user_model()
        subject = f'New Awareness Program: {awareness.title}'
        
        users = User.objects.all()
        recipient_list = [user.email for user in users if user.email]
        
        if recipient_list:
            # Render the email template
            html_content = render_to_string('awareness/awareness_email.html', {
                'awareness': awareness,
                'subject': subject,
                'site_url': settings.SITE_URL,
            })
            
            # Create the email
            email = EmailMultiAlternatives(
                subject,
                '',  # Plain text content
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()