from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from awareness.models import Awareness
from contact.forms import ContactEnquiryForm
from contact.utils import send_enquiry_notification_to_admin, send_confirmation_to_user
import json
from datetime import datetime
# from django.contrib.auth.decorators import login_required

def home(request):
    awareness = Awareness.objects.all().order_by('-created_at')[:6]
    
    # Handle contact form submission
    if request.method == 'POST':
        form = ContactEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save(commit=False)
            
            # Link to user if authenticated
            if request.user.is_authenticated:
                enquiry.user = request.user
                # Pre-fill user data if not provided
                if not enquiry.first_name:
                    enquiry.first_name = request.user.first_name
                if not enquiry.last_name:
                    enquiry.last_name = request.user.last_name
                if not enquiry.email:
                    enquiry.email = request.user.email
                if not enquiry.phone:
                    enquiry.phone = request.user.phone_number
            
            enquiry.save()
            
            # Send emails
            send_confirmation_to_user(enquiry)
            send_enquiry_notification_to_admin(enquiry)
            
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # Pre-fill form if user is authenticated
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone': request.user.phone_number,
            }
        form = ContactEnquiryForm(initial=initial_data)
    
    context = {
        'awareness': awareness,
        'contact_form': form
    }
    return render(request, 'home.html', context)


@require_POST
@csrf_exempt
def emergency_alert(request):
    """Handle emergency alert notifications"""
    try:
        data = json.loads(request.body)
        user_name = data.get('user_name', 'Anonymous User')
        user_email = data.get('user_email', 'Not provided')
        user_phone = data.get('user_phone', 'Not provided')
        user_location = data.get('user_location', 'Not provided')
        google_maps_link = data.get('google_maps_link', 'Not available')
        
        # Prepare email content
        subject = f'🚨 EMERGENCY ALERT - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # HTML email with Google Maps link
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 3px solid #dc2626; border-radius: 10px; background-color: #fef2f2;">
                <div style="background-color: #dc2626; color: white; padding: 20px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 28px;">🚨 EMERGENCY ALERT</h1>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Immediate Action Required</p>
                </div>
                
                <div style="background-color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                    <h2 style="color: #dc2626; margin-top: 0;">User Details:</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Name:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{user_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Email:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{user_email}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Phone:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><a href="tel:{user_phone}" style="color: #dc2626; font-weight: bold; font-size: 18px;">{user_phone}</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Time:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #dbeafe; padding: 20px; border-radius: 5px; border-left: 4px solid #2563eb; margin-bottom: 20px;">
                    <h3 style="color: #1e40af; margin-top: 0;">📍 User Location:</h3>
                    {f'<p style="margin: 10px 0;"><a href="{google_maps_link}" target="_blank" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">📍 Open Location in Google Maps</a></p>' if google_maps_link != 'Not available' else '<p style="color: #991b1b; font-weight: bold;">Location not available</p>'}
                    <p style="font-size: 12px; color: #6b7280; margin-top: 10px;">Click the button above to see the exact location on Google Maps</p>
                </div>
                
                <div style="background-color: #fee2e2; padding: 20px; border-radius: 5px; border-left: 4px solid #dc2626;">
                    <h3 style="color: #991b1b; margin-top: 0;">⚡ Action Required:</h3>
                    <p style="margin: 5px 0;"><strong>This is an automated emergency alert from the Rural Health Chatbot system.</strong></p>
                    <p style="margin: 5px 0;">Please contact the user <strong>IMMEDIATELY</strong>.</p>
                    
                    <div style="margin-top: 15px; padding: 15px; background-color: white; border-radius: 5px;">
                        <p style="margin: 0 0 10px 0; font-weight: bold; color: #dc2626;">Emergency Contact Numbers:</p>
                        <p style="margin: 5px 0; font-size: 20px; font-weight: bold;"><a href="tel:9839096052" style="color: #dc2626; text-decoration: none;">📞 9839096052</a></p>
                        <p style="margin: 5px 0; font-size: 20px; font-weight: bold;"><a href="tel:9807973936" style="color: #dc2626; text-decoration: none;">📞 9807973936</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        plain_message = f"""
🚨 EMERGENCY ALERT - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

User Details:
- Name: {user_name}
- Email: {user_email}
- Phone: {user_phone}
- Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Location:
{f'View on Google Maps: {google_maps_link}' if google_maps_link != 'Not available' else 'Location not available'}

This is an automated emergency alert from the Rural Health Chatbot system.
Please contact the user IMMEDIATELY.

Emergency Contact Numbers:
- 9839096052
- 9807973936
        """
        
        # Send email to admin
        try:
            from django.core.mail import EmailMessage
            
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],  # Send to admin email
            )
            email.content_subtype = 'html'  # Set content type to HTML
            email.send(fail_silently=False)
            
            return JsonResponse({
                'success': True,
                'message': 'Emergency alert sent successfully',
                'phone_number': '9839096052'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'phone_number': '9839096052'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error processing emergency alert: {str(e)}'
        }, status=400)


# # import the appointment model and use as context in the dashboard view
# from appointments.models import Appointment
# from django.utils import timezone

# @login_required
# def healthworker_dashboard(request):
#     appointments = Appointment.objects.filter(health_worker=request.user).order_by('-date')
#     today = timezone.localdate()
#     today_appointments = appointments.filter(date__exact=today)
#     today_pending = today_appointments.filter(status='pending')
#     today_confirmed = today_appointments.filter(status='confirmed')
#     today_completed = today_appointments.filter(status='completed')
#     today_canceled = today_appointments.filter(status='canceled')
#     today_count = today_appointments.count()
#     pending = appointments.filter(status='pending')
#     confirmed = appointments.filter(status='confirmed')
#     completed = appointments.filter(status='completed')
#     canceled = appointments.filter(status='canceled')
#     context = {
#         'appointments': appointments,
#         'pending': pending,
#         'confirmed': confirmed,
#         'completed': completed,
#         'canceled': canceled,
#         'today_count': today_count,
#         'today_pending': today_pending,
#         'today_confirmed': today_confirmed,
#         'today_completed': today_completed,
#         'today_canceled': today_canceled,
#     }
#     return render(request, 'healthworkerdashboard/index.html', context)


# Custom Error Handlers
def custom_400(request, exception):
    """Custom 400 error handler"""
    return render(request, '400.html', status=400)


def custom_403(request, exception):
    """Custom 403 error handler"""
    return render(request, '403.html', status=403)


def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error handler"""
    return render(request, '500.html', status=500)
