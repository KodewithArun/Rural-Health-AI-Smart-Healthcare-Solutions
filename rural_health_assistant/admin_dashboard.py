# rural_health_assistant/admin_dashboard.py
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime
from accounts.models import Account, HealthWorkerProfile
from appointments.models import Appointment
from chat.models import ChatHistory
from contact.models import ContactEnquiry
from documents.models import Document
from awareness.models import Awareness
import json


@staff_member_required
def dashboard_view(request):
    """Main dashboard view with analytics"""
    
    # Time periods
    now = timezone.now()
    today = now.date()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    this_month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    
    # ========== USER STATISTICS ==========
    total_users = Account.objects.count()
    villagers_count = Account.objects.filter(role='villager').count()
    health_workers_count = Account.objects.filter(role='health_worker').count()
    admins_count = Account.objects.filter(role='admin').count()
    
    # New users (last 7 days)
    new_users_week = Account.objects.filter(date_joined__gte=last_7_days).count()
    new_users_month = Account.objects.filter(date_joined__gte=last_30_days).count()
    
    # Active users (users who chatted in last 7 days)
    active_users_week = ChatHistory.objects.filter(
        timestamp__gte=last_7_days
    ).values('user').distinct().count()
    
    # ========== APPOINTMENT STATISTICS ==========
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    approved_appointments = Appointment.objects.filter(status='approved').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(date=today).count()
    
    # Upcoming appointments (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_appointments = Appointment.objects.filter(
        date__gte=today,
        date__lte=next_week,
        status__in=['pending', 'approved']
    ).count()
    
    # Appointments this month
    appointments_this_month = Appointment.objects.filter(
        created_at__gte=this_month_start
    ).count()
    
    # Recent appointments (last 5)
    recent_appointments = Appointment.objects.select_related(
        'villager', 'healthworker'
    ).order_by('-created_at')[:5]
    
    # ========== CHAT STATISTICS ==========
    total_chats = ChatHistory.objects.count()
    chats_today = ChatHistory.objects.filter(timestamp__date=today).count()
    chats_this_week = ChatHistory.objects.filter(timestamp__gte=last_7_days).count()
    chats_this_month = ChatHistory.objects.filter(timestamp__gte=last_30_days).count()
    
    # Average chats per user
    avg_chats_per_user = ChatHistory.objects.values('user').annotate(
        chat_count=Count('id')
    ).aggregate(average=Avg('chat_count'))['average'] or 0
    
    # Most active users (top 5 by chat count)
    most_active_users = ChatHistory.objects.values(
        'user__username', 'user__first_name', 'user__last_name', 'user__role'
    ).annotate(
        chat_count=Count('id')
    ).order_by('-chat_count')[:5]
    
    # Recent chats (last 5)
    recent_chats = ChatHistory.objects.select_related('user').order_by('-timestamp')[:5]
    
    # ========== DOCUMENT STATISTICS ==========
    total_documents = Document.objects.count()
    documents_this_month = Document.objects.filter(
        created_at__gte=this_month_start
    ).count()
    
    # Recent documents (last 5)
    recent_documents = Document.objects.select_related('uploaded_by').order_by('-created_at')[:5]
    
    # ========== CONTACT ENQUIRY STATISTICS ==========
    total_enquiries = ContactEnquiry.objects.count()
    pending_enquiries = ContactEnquiry.objects.filter(status='pending').count()
    in_progress_enquiries = ContactEnquiry.objects.filter(status='in_progress').count()
    resolved_enquiries = ContactEnquiry.objects.filter(status='resolved').count()
    
    # Enquiries this week
    enquiries_this_week = ContactEnquiry.objects.filter(
        created_at__gte=last_7_days
    ).count()
    
    # Recent enquiries (last 5)
    recent_enquiries = ContactEnquiry.objects.order_by('-created_at')[:5]
    
    # ========== AWARENESS STATISTICS ==========
    total_awareness = Awareness.objects.count()
    awareness_events = Awareness.objects.filter(is_event=True).count()
    awareness_posts = Awareness.objects.filter(is_event=False).count()
    
    # Upcoming events
    upcoming_events = Awareness.objects.filter(
        is_event=True,
        event_date__gte=today
    ).order_by('event_date')[:5]
    
    # Recent awareness posts
    recent_awareness = Awareness.objects.order_by('-created_at')[:5]
    
    # ========== HEALTH WORKER STATISTICS ==========
    available_health_workers = HealthWorkerProfile.objects.filter(
        availability=True
    ).count()
    
    # Health workers with most appointments
    top_health_workers = Appointment.objects.filter(
        healthworker__isnull=False
    ).values(
        'healthworker__username',
        'healthworker__first_name',
        'healthworker__last_name'
    ).annotate(
        appointment_count=Count('id')
    ).order_by('-appointment_count')[:5]
    
    # ========== TREND DATA FOR CHARTS ==========
    # Last 7 days appointment trend
    appointment_trend = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Appointment.objects.filter(created_at__date=date).count()
        appointment_trend.append({
            'date': date.strftime('%b %d'),
            'count': count
        })
    
    # Last 7 days chat trend
    chat_trend = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = ChatHistory.objects.filter(timestamp__date=date).count()
        chat_trend.append({
            'date': date.strftime('%b %d'),
            'count': count
        })
    
    # ========== CONTEXT DATA ==========
    # Start with admin site context to include sidebar
    context = admin.site.each_context(request)
    
    # Add dashboard-specific data
    dashboard_data = {
        'title': 'Dashboard & Analytics',
        
        # User stats
        'total_users': total_users,
        'villagers_count': villagers_count,
        'health_workers_count': health_workers_count,
        'admins_count': admins_count,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'active_users_week': active_users_week,
        
        # Appointment stats
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'appointments_this_month': appointments_this_month,
        'recent_appointments': recent_appointments,
        'appointment_trend': json.dumps(appointment_trend),
        
        # Chat stats
        'total_chats': total_chats,
        'chats_today': chats_today,
        'chats_this_week': chats_this_week,
        'chats_this_month': chats_this_month,
        'avg_chats_per_user': round(avg_chats_per_user, 1),
        'most_active_users': most_active_users,
        'recent_chats': recent_chats,
        'chat_trend': json.dumps(chat_trend),
        
        # Document stats
        'total_documents': total_documents,
        'documents_this_month': documents_this_month,
        'recent_documents': recent_documents,
        
        # Enquiry stats
        'total_enquiries': total_enquiries,
        'pending_enquiries': pending_enquiries,
        'in_progress_enquiries': in_progress_enquiries,
        'resolved_enquiries': resolved_enquiries,
        'enquiries_this_week': enquiries_this_week,
        'recent_enquiries': recent_enquiries,
        
        # Awareness stats
        'total_awareness': total_awareness,
        'awareness_events': awareness_events,
        'awareness_posts': awareness_posts,
        'upcoming_events': upcoming_events,
        'recent_awareness': recent_awareness,
        
        # Health worker stats
        'available_health_workers': available_health_workers,
        'top_health_workers': top_health_workers,
        
        # Current date
        'current_date': now,
    }
    
    # Merge dashboard data into admin context
    context.update(dashboard_data)
    
    return render(request, 'admin/dashboard.html', context)
