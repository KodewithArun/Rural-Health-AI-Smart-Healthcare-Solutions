from django.shortcuts import render
from awareness.models import Awareness
# from django.contrib.auth.decorators import login_required

def home(request):
    awareness = Awareness.objects.all().order_by('-created_at')[:6]
    context = {'awareness': awareness}
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
