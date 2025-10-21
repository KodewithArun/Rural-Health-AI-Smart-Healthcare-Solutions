from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_enquiry_notification_to_admin(enquiry):
    """Send email notification to all admin users when a new enquiry is submitted"""
    from accounts.models import Account
    
    # Get all admin users
    admin_users = Account.objects.filter(is_admin=True, is_active=True)
    admin_emails = [admin.email for admin in admin_users if admin.email]
    
    if not admin_emails:
        return False
    
    subject = f'New Contact Enquiry from {enquiry.first_name} {enquiry.last_name}'
    
    # Create HTML email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                New Contact Enquiry Received
            </h2>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Enquiry Details:</h3>
                <p><strong>Name:</strong> {enquiry.first_name} {enquiry.last_name}</p>
                <p><strong>Email:</strong> {enquiry.email}</p>
                <p><strong>Phone:</strong> {enquiry.phone}</p>
                <p><strong>Date:</strong> {enquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #1f2937;">Message:</h3>
                <div style="background-color: #f9fafb; padding: 15px; border-left: 4px solid #2563eb; border-radius: 5px;">
                    {enquiry.message}
                </div>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #6b7280; font-size: 14px;">
                    Please log in to the admin panel to respond to this enquiry.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    New Contact Enquiry Received
    
    Enquiry Details:
    Name: {enquiry.first_name} {enquiry.last_name}
    Email: {enquiry.email}
    Phone: {enquiry.phone}
    Date: {enquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}
    
    Message:
    {enquiry.message}
    
    Please log in to the admin panel to respond to this enquiry.
    """
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending admin notification: {e}")
        return False


def send_response_to_user(enquiry):
    """Send admin response email to the user"""
    subject = f'Response to Your Enquiry - Rural Health AI'
    
    # Create HTML email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin: 0;">Rural Health AI</h1>
                <p style="color: #6b7280; margin: 5px 0;">Smart Healthcare Solutions</p>
            </div>
            
            <h2 style="color: #1f2937; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                Response to Your Enquiry
            </h2>
            
            <p style="color: #4b5563;">Dear {enquiry.first_name} {enquiry.last_name},</p>
            
            <p style="color: #4b5563;">
                Thank you for contacting Rural Health AI. We have reviewed your enquiry and here is our response:
            </p>
            
            <div style="background-color: #eff6ff; padding: 20px; border-left: 4px solid #2563eb; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1e40af;">Admin Response:</h3>
                <p style="white-space: pre-line; color: #1f2937;">{enquiry.admin_response}</p>
            </div>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1f2937;">Your Original Message:</h4>
                <p style="color: #6b7280; font-style: italic;">{enquiry.message}</p>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #4b5563;">
                    If you have any further questions, please don't hesitate to contact us again.
                </p>
                <p style="color: #4b5563; margin-bottom: 0;">
                    Best regards,<br>
                    <strong>Rural Health AI Team</strong>
                </p>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #fef2f2; border-left: 4px solid #dc2626; border-radius: 5px;">
                <p style="color: #991b1b; font-size: 13px; margin: 0;">
                    <strong>Medical Emergency Notice:</strong> If you are experiencing a medical emergency, 
                    please call 911 immediately or go to your nearest emergency room.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Response to Your Enquiry - Rural Health AI
    
    Dear {enquiry.first_name} {enquiry.last_name},
    
    Thank you for contacting Rural Health AI. We have reviewed your enquiry and here is our response:
    
    Admin Response:
    {enquiry.admin_response}
    
    Your Original Message:
    {enquiry.message}
    
    If you have any further questions, please don't hesitate to contact us again.
    
    Best regards,
    Rural Health AI Team
    
    ---
    Medical Emergency Notice: If you are experiencing a medical emergency, 
    please call 911 immediately or go to your nearest emergency room.
    """
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[enquiry.email],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending user response: {e}")
        return False


def send_confirmation_to_user(enquiry):
    """Send confirmation email to user after they submit an enquiry"""
    subject = 'We Received Your Enquiry - Rural Health AI'
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2563eb; margin: 0;">Rural Health AI</h1>
                <p style="color: #6b7280; margin: 5px 0;">Smart Healthcare Solutions</p>
            </div>
            
            <div style="background-color: #dcfce7; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                <h2 style="color: #166534; margin: 0;">✓ Enquiry Received Successfully</h2>
            </div>
            
            <p style="color: #4b5563;">Dear {enquiry.first_name} {enquiry.last_name},</p>
            
            <p style="color: #4b5563;">
                Thank you for reaching out to Rural Health AI. We have received your enquiry and our team will review it shortly.
            </p>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Your Enquiry Details:</h3>
                <p><strong>Reference Date:</strong> {enquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                <p><strong>Email:</strong> {enquiry.email}</p>
                <p><strong>Phone:</strong> {enquiry.phone}</p>
            </div>
            
            <div style="background-color: #f9fafb; padding: 15px; border-left: 4px solid #2563eb; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #1f2937;">Your Message:</h4>
                <p style="color: #6b7280;">{enquiry.message}</p>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #4b5563;">
                    Our team typically responds within 24-48 hours. You will receive an email at <strong>{enquiry.email}</strong> once we have reviewed your enquiry.
                </p>
                <p style="color: #4b5563; margin-bottom: 0;">
                    Best regards,<br>
                    <strong>Rural Health AI Team</strong>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    We Received Your Enquiry - Rural Health AI
    
    Dear {enquiry.first_name} {enquiry.last_name},
    
    Thank you for reaching out to Rural Health AI. We have received your enquiry and our team will review it shortly.
    
    Your Enquiry Details:
    Reference Date: {enquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}
    Email: {enquiry.email}
    Phone: {enquiry.phone}
    
    Your Message:
    {enquiry.message}
    
    Our team typically responds within 24-48 hours. You will receive an email at {enquiry.email} once we have reviewed your enquiry.
    
    Best regards,
    Rural Health AI Team
    """
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[enquiry.email],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending confirmation: {e}")
        return False
