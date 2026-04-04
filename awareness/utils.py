from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
import threading


def send_awareness_email_async(awareness, site_url):
    """
    Sends an email to all active users about a new awareness post.
    Run asynchronously to avoid blocking the request.
    """
    User = get_user_model()
    subject = f"New Awareness Program: {awareness.title}"

    # Only send to users who have email addresses and are active
    users = User.objects.filter(email__isnull=False, is_active=True).exclude(email="")
    recipient_list = [user.email for user in users]

    if recipient_list:
        context = {
            "awareness": awareness,
            "subject": subject,
            "site_url": site_url,
        }

        try:
            html_content = render_to_string("awareness/awareness_email.html", context)
        except Exception:
            # Fallback if html template is missing
            html_content = ""

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
            plain_text_content,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
        )
        if html_content:
            email.attach_alternative(html_content, "text/html")

        try:
            email.send(fail_silently=True)
        except Exception as e:
            # Let it fail silently in the thread
            pass


def trigger_awareness_email(awareness, request):
    site_url = getattr(settings, "SITE_URL", request.build_absolute_uri("/")[:-1])
    email_thread = threading.Thread(
        target=send_awareness_email_async, args=(awareness, site_url)
    )
    email_thread.start()
