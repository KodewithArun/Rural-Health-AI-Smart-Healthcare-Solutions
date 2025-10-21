from django.shortcuts import render, redirect
from django.contrib import messages
from awareness.models import Awareness
from contact.forms import ContactEnquiryForm
from contact.utils import send_enquiry_notification_to_admin, send_confirmation_to_user
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
