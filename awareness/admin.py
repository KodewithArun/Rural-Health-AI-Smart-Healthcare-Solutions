# from django.contrib import admin
from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from .models import Awareness

@admin.register(Awareness)
class AwarenessAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_date_display', 'created_at', 'is_event')
    list_filter = ('is_event', 'event_date')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_event', 'event_date')
        }),
        ('Media', {
            'fields': ('photo', 'pdf')
        }),
    )
    
    class Media:
        js = ('js/awareness_admin.js',)
    class Media:
        js = ('js/awareness_admin.js',)
    
    def get_date_display(self, obj):
        if obj.event_date:
            return obj.event_date
        return "N/A (Informational)"
    get_date_display.short_description = 'Date'
    
    def save_model(self, request, obj, form, change):
        # Save the model first
        super().save_model(request, obj, form, change)

        # Only send email on creation (not updates)
        if not change:
            try:
                self.send_awareness_email(obj)
                messages.success(request, f'Awareness item "{obj.title}" created and notification emails sent.')
            except Exception as e:
                messages.error(request, f'Awareness item saved but email notification failed: {str(e)}')
    
    def send_awareness_email(self, awareness):
        User = get_user_model()
        subject = f'New Awareness Program: {awareness.title}'

        # Only send to users who have email addresses and are active
        users = User.objects.filter(email__isnull=False, is_active=True).exclude(email='')
        recipient_list = [user.email for user in users]

        if recipient_list:
            # Get site URL from settings with fallback
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

            # Render both HTML and plain text content
            html_content = render_to_string('awareness/awareness_email.html', {
                'awareness': awareness,
                'subject': subject,
                'site_url': site_url,
            })

            # Create plain text version
            plain_text_content = f"""
New Awareness Program: {awareness.title}

{awareness.description}

{'Event Date: ' + str(awareness.event_date) if awareness.event_date else ''}

Visit our portal for more details: {site_url}
            """.strip()

            # Create the email with both HTML and plain text
            email = EmailMultiAlternatives(
                subject,
                plain_text_content,  # Plain text content
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()