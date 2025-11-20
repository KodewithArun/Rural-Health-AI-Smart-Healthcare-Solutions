from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Appointment
from .forms import AppointmentForm, AppointmentUpdateForm
from .utils import send_appointment_email, classify_appointment_priority, get_prioritized_appointments

# User role checks
def is_villager(user):
    return user.role == 'villager'

def is_health_worker(user):
    return user.role == 'health_worker'

def is_admin(user):
    return user.role == 'admin'

def can_access_appointment(user, appointment):
    return (
        user.role == 'admin' or 
        (user.role == 'health_worker' and appointment.healthworker == user) or
        (user.role == 'villager' and appointment.villager == user)
    )

# List appointments
@login_required
def appointment_list(request):
    if is_villager(request.user):
        appointments = Appointment.objects.filter(villager=request.user)
        # Sort villager appointments by priority too (they can see urgency)
        appointments = get_prioritized_appointments(appointments)
        # Add can_cancel attribute after sorting (works on list)
        for appt in appointments:
            appt.can_cancel = can_villager_cancel(appt)
    elif is_health_worker(request.user):
        appointments = Appointment.objects.filter(healthworker=request.user)
        # Sort appointments by priority using the priority queue
        appointments = get_prioritized_appointments(appointments)
    elif is_admin(request.user):
        appointments = Appointment.objects.all()
        # Sort appointments by priority for admin view as well
        appointments = get_prioritized_appointments(appointments)
    else:
        return HttpResponseForbidden()
    
    # Calculate statistics
    today = timezone.now().date()
    
    # Convert to list if it's already a list from priority queue
    if isinstance(appointments, list):
        total_count = len(appointments)
        pending_count = len([a for a in appointments if a.status == 'pending'])
        approved_count = len([a for a in appointments if a.status == 'approved'])
        completed_count = len([a for a in appointments if a.status == 'completed'])
        cancelled_count = len([a for a in appointments if a.status == 'cancelled'])
        upcoming_count = len([a for a in appointments if a.date >= today and a.status in ['pending', 'approved']])
        
        # Count by priority
        critical_count = len([a for a in appointments if a.priority == 'critical'])
        medium_count = len([a for a in appointments if a.priority == 'medium'])
        normal_count = len([a for a in appointments if a.priority == 'normal'])
    else:
        # QuerySet
        total_count = appointments.count()
        pending_count = appointments.filter(status='pending').count()
        approved_count = appointments.filter(status='approved').count()
        completed_count = appointments.filter(status='completed').count()
        cancelled_count = appointments.filter(status='cancelled').count()
        
        # Upcoming appointments (future dates with pending or approved status)
        upcoming_count = appointments.filter(
            date__gte=today,
            status__in=['pending', 'approved']
        ).count()
        
        # Count by priority
        critical_count = appointments.filter(priority='critical').count()
        medium_count = appointments.filter(priority='medium').count()
        normal_count = appointments.filter(priority='normal').count()
    
    context = {
        'appointments': appointments,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'upcoming_count': upcoming_count,
        'critical_count': critical_count,
        'medium_count': medium_count,
        'normal_count': normal_count,
    }
    
    return render(request, 'appointments/appointment_list.html', context)


# View appointment details
@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user has permission to view this appointment
    if not can_access_appointment(request.user, appointment):
        return HttpResponseForbidden("You don't have permission to view this appointment.")
    
    # For villagers, check if they can cancel
    can_cancel = False
    if is_villager(request.user):
        can_cancel = can_villager_cancel(appointment)
    
    context = {
        'appointment': appointment,
        'can_cancel': can_cancel,
    }
    return render(request, 'appointments/appointment_detail.html', context)

# Create appointment
@login_required
@user_passes_test(is_villager)
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.villager = request.user
            
            # Classify appointment priority using AI
            reason = form.cleaned_data.get('reason', '')
            appointment.priority = classify_appointment_priority(reason)
            
            appointment.save()
            send_appointment_email(appointment, created=True)
            return redirect('appointments:list')
    else:
        form = AppointmentForm(user=request.user)
    
    return render(request, 'appointments/villager/appointment_form.html', {'form': form})

# Update appointment
@login_required
def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not can_access_appointment(request.user, appointment) or is_villager(request.user):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            send_appointment_email(appointment, created=False)
            return redirect('appointments:list')
    else:
        form = AppointmentUpdateForm(instance=appointment, user=request.user)
    
    return render(request, 'appointments/health_worker/appointment_update.html', {'form': form, 'appointment': appointment})

# Delete appointment
@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if not can_access_appointment(request.user, appointment) or is_villager(request.user):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        appointment.delete()
        return redirect('appointments:list')
    
    return render(request, 'appointments/appointment_confirm_delete.html', {'appointment': appointment})

# Villager cancel appointment
@login_required
@user_passes_test(is_villager)
def villager_cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, villager=request.user)
    if not can_villager_cancel(appointment):
        return HttpResponseForbidden("You can only cancel appointments that are at least 24 hours away.")
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        send_appointment_email(appointment, created=False)
        return redirect('appointments:list')
    
    return render(request, 'appointments/villager/appointment_cancel_confirm.html', {'appointment': appointment})

# Helper: Can villager cancel?
def can_villager_cancel(appointment):
    if appointment.status == 'cancelled':
        return False
    appointment_datetime = datetime.combine(appointment.date, appointment.time)
    appointment_datetime = timezone.make_aware(appointment_datetime)
    return (appointment_datetime - timezone.now()) >= timedelta(hours=24)

# Auto-cancel no-show appointments
def auto_cancel_no_show_appointments():
    now = timezone.now()
    overdue_appointments = Appointment.objects.filter(
        status__in=['pending', 'approved'],
        date__lte=now.date()
    )
    overdue_appointments_today = overdue_appointments.filter(
        date=now.date(),
        time__lt=(now - timedelta(minutes=30)).time()
    )
    overdue_appointments_previous = overdue_appointments.filter(date__lt=now.date())
    
    all_overdue = overdue_appointments_today | overdue_appointments_previous
    count = all_overdue.update(status='cancelled')
    
    for appt in all_overdue:
        send_appointment_email(appt, created=False)
    
    return count
