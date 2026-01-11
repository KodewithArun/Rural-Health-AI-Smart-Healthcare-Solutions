# rural_health_assistant/admin_views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from datetime import timedelta, datetime
from accounts.models import Account, HealthWorkerProfile
from accounts.forms import HealthWorkerCreationForm
from appointments.models import Appointment
from chat.models import ChatHistory
from contact.models import ContactEnquiry
from documents.models import Document
from documents.forms import DocumentUploadForm
from awareness.models import Awareness
from awareness.forms import AwarenessForm
import json
import csv


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_superadmin or user.role == "admin")


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard with analytics"""

    # Time periods
    now = timezone.now()
    today = now.date()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    this_month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

    # ========== USER STATISTICS ==========
    total_users = Account.objects.count()
    villagers_count = Account.objects.filter(role="villager").count()
    health_workers_count = Account.objects.filter(role="health_worker").count()
    admins_count = Account.objects.filter(role="admin").count()
    new_users_week = Account.objects.filter(date_joined__gte=last_7_days).count()
    active_users_week = (
        ChatHistory.objects.filter(timestamp__gte=last_7_days)
        .values("user")
        .distinct()
        .count()
    )

    # ========== APPOINTMENT STATISTICS ==========
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status="pending").count()
    approved_appointments = Appointment.objects.filter(status="approved").count()
    completed_appointments = Appointment.objects.filter(status="completed").count()
    cancelled_appointments = Appointment.objects.filter(status="cancelled").count()
    today_appointments = Appointment.objects.filter(date=today).count()
    recent_appointments = Appointment.objects.select_related(
        "villager", "healthworker"
    ).order_by("-created_at")[:5]

    # ========== CHAT STATISTICS ==========
    total_chats = ChatHistory.objects.count()
    chats_today = ChatHistory.objects.filter(timestamp__date=today).count()
    chats_this_week = ChatHistory.objects.filter(timestamp__gte=last_7_days).count()
    most_active_users = (
        ChatHistory.objects.values(
            "user__username", "user__first_name", "user__last_name", "user__role"
        )
        .annotate(chat_count=Count("id"))
        .order_by("-chat_count")[:5]
    )

    # ========== OTHER STATISTICS ==========
    total_documents = Document.objects.count()
    documents_this_month = Document.objects.filter(
        created_at__gte=this_month_start
    ).count()
    total_enquiries = ContactEnquiry.objects.count()
    pending_enquiries = ContactEnquiry.objects.filter(status="pending").count()
    total_awareness = Awareness.objects.count()
    awareness_events = Awareness.objects.filter(is_event=True).count()

    # Recent items
    recent_enquiries = ContactEnquiry.objects.order_by("-created_at")[:5]
    recent_documents = Document.objects.select_related("uploaded_by").order_by(
        "-created_at"
    )[:5]
    upcoming_events = Awareness.objects.filter(
        is_event=True, event_date__gte=today
    ).order_by("event_date")[:5]

    # Top health workers
    top_health_workers = (
        Appointment.objects.filter(healthworker__isnull=False)
        .values(
            "healthworker__username",
            "healthworker__first_name",
            "healthworker__last_name",
        )
        .annotate(appointment_count=Count("id"))
        .order_by("-appointment_count")[:5]
    )

    # ========== TREND DATA FOR CHARTS ==========
    appointment_trend = []
    chat_trend = []
    user_trend = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        appointment_trend.append(
            {
                "date": date.strftime("%b %d"),
                "count": Appointment.objects.filter(created_at__date=date).count(),
            }
        )
        chat_trend.append(
            {
                "date": date.strftime("%b %d"),
                "count": ChatHistory.objects.filter(timestamp__date=date).count(),
            }
        )
        user_trend.append(
            {
                "date": date.strftime("%b %d"),
                "count": Account.objects.filter(date_joined__date=date).count(),
            }
        )

    context = {
        "title": "Admin Dashboard",
        "total_users": total_users,
        "villagers_count": villagers_count,
        "health_workers_count": health_workers_count,
        "admins_count": admins_count,
        "new_users_week": new_users_week,
        "active_users_week": active_users_week,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "approved_appointments": approved_appointments,
        "completed_appointments": completed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "today_appointments": today_appointments,
        "recent_appointments": recent_appointments,
        "total_chats": total_chats,
        "chats_today": chats_today,
        "chats_this_week": chats_this_week,
        "most_active_users": most_active_users,
        "total_documents": total_documents,
        "documents_this_month": documents_this_month,
        "total_enquiries": total_enquiries,
        "pending_enquiries": pending_enquiries,
        "total_awareness": total_awareness,
        "awareness_events": awareness_events,
        "recent_enquiries": recent_enquiries,
        "recent_documents": recent_documents,
        "upcoming_events": upcoming_events,
        "top_health_workers": top_health_workers,
        "appointment_trend": json.dumps(appointment_trend),
        "chat_trend": json.dumps(chat_trend),
        "user_trend": json.dumps(user_trend),
        "current_date": now,
    }

    return render(request, "custom_admin/dashboard.html", context)


# ==================== USER MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users with filtering and search"""
    users = Account.objects.all()

    # Filtering
    role = request.GET.get("role")
    status = request.GET.get("status")
    search = request.GET.get("search")

    if role:
        users = users.filter(role=role)
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)
    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    users = users.order_by("-date_joined")

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "User Management",
        "page_obj": page_obj,
        "role": role,
        "status": status,
        "search": search,
    }
    return render(request, "custom_admin/users/list.html", context)


@login_required
@user_passes_test(is_admin)
def user_create_healthworker(request):
    """Create a new health worker"""
    if request.method == "POST":
        form = HealthWorkerCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"Health worker {user.username} has been created successfully."
            )
            return redirect("custom_admin:user_detail", user_id=user.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = HealthWorkerCreationForm()

    context = {
        "title": "Create Health Worker",
        "form": form,
    }
    return render(request, "custom_admin/users/create_healthworker.html", context)


@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(Account, id=user_id)

    # Get user statistics
    user_appointments = Appointment.objects.filter(villager=user).count()
    user_chats = ChatHistory.objects.filter(user=user).count()

    if user.role == "health_worker":
        assigned_appointments = Appointment.objects.filter(healthworker=user).count()
        health_profile = HealthWorkerProfile.objects.filter(user=user).first()
    else:
        assigned_appointments = 0
        health_profile = None

    context = {
        "title": f"User: {user.username}",
        "user_obj": user,
        "user_appointments": user_appointments,
        "user_chats": user_chats,
        "assigned_appointments": assigned_appointments,
        "health_profile": health_profile,
    }
    return render(request, "custom_admin/users/detail.html", context)


@login_required
@user_passes_test(is_admin)
def user_toggle_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(Account, id=user_id)
    user.is_active = not user.is_active
    user.save()

    # If health worker, also update availability
    if user.role == "health_worker":
        try:
            health_profile = HealthWorkerProfile.objects.get(user=user)
            health_profile.availability = user.is_active
            health_profile.save()
        except HealthWorkerProfile.DoesNotExist:
            pass

    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status}.")

    return redirect("custom_admin:user_detail", user_id=user_id)


@login_required
@user_passes_test(is_admin)
def user_delete(request, user_id):
    """Delete a user"""
    user = get_object_or_404(Account, id=user_id)

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"User {username} has been deleted.")
        return redirect("custom_admin:user_list")

    context = {
        "title": "Delete User",
        "user_obj": user,
    }
    return render(request, "custom_admin/users/delete.html", context)


# ==================== APPOINTMENT MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def appointment_list(request):
    """List all appointments"""
    appointments = Appointment.objects.select_related("villager", "healthworker").all()

    # Filtering
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    search = request.GET.get("search")

    if status:
        appointments = appointments.filter(status=status)
    if priority:
        appointments = appointments.filter(priority=priority)
    if search:
        appointments = appointments.filter(
            Q(villager__first_name__icontains=search)
            | Q(villager__last_name__icontains=search)
            | Q(healthworker__first_name__icontains=search)
            | Q(healthworker__last_name__icontains=search)
            | Q(reason__icontains=search)
        )

    appointments = appointments.order_by("-created_at")

    # Pagination
    paginator = Paginator(appointments, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Appointment Management",
        "page_obj": page_obj,
        "status": status,
        "priority": priority,
        "search": search,
    }
    return render(request, "custom_admin/appointments/list.html", context)


@login_required
@user_passes_test(is_admin)
def appointment_detail(request, appointment_id):
    """View appointment details"""
    appointment = get_object_or_404(
        Appointment.objects.select_related("villager", "healthworker"),
        id=appointment_id,
    )

    context = {
        "title": f"Appointment #{appointment.id}",
        "appointment": appointment,
    }
    return render(request, "custom_admin/appointments/detail.html", context)


@login_required
@user_passes_test(is_admin)
def appointment_update_status(request, appointment_id):
    """Update appointment status"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        note = request.POST.get("note", "")

        if new_status in ["pending", "approved", "completed", "cancelled"]:
            appointment.status = new_status
            if note:
                appointment.note = note
            appointment.save()
            messages.success(request, f"Appointment status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status.")

    return redirect("custom_admin:appointment_detail", appointment_id=appointment_id)


@login_required
@user_passes_test(is_admin)
def appointment_assign(request, appointment_id):
    """Assign health worker to appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        health_worker_id = request.POST.get("health_worker")
        health_worker = get_object_or_404(
            Account, id=health_worker_id, role="health_worker"
        )

        appointment.healthworker = health_worker
        appointment.save()
        messages.success(
            request, f"Appointment assigned to {health_worker.get_full_name()}."
        )
        return redirect(
            "custom_admin:appointment_detail", appointment_id=appointment_id
        )

    health_workers = Account.objects.filter(role="health_worker", is_active=True)

    context = {
        "title": "Assign Health Worker",
        "appointment": appointment,
        "health_workers": health_workers,
    }
    return render(request, "custom_admin/appointments/assign.html", context)


@login_required
@user_passes_test(is_admin)
def appointment_delete(request, appointment_id):
    """Delete an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        appointment.delete()
        messages.success(request, "Appointment has been deleted.")
        return redirect("custom_admin:appointment_list")

    context = {
        "title": "Delete Appointment",
        "appointment": appointment,
    }
    return render(request, "custom_admin/appointments/delete.html", context)


# ==================== ENQUIRY MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def enquiry_list(request):
    """List all contact enquiries"""
    enquiries = ContactEnquiry.objects.select_related("user", "responded_by").all()

    # Filtering
    status = request.GET.get("status")
    search = request.GET.get("search")

    if status:
        enquiries = enquiries.filter(status=status)
    if search:
        enquiries = enquiries.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(message__icontains=search)
        )

    enquiries = enquiries.order_by("-created_at")

    # Pagination
    paginator = Paginator(enquiries, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Contact Enquiries",
        "page_obj": page_obj,
        "status": status,
        "search": search,
    }
    return render(request, "custom_admin/enquiries/list.html", context)


@login_required
@user_passes_test(is_admin)
def enquiry_detail(request, enquiry_id):
    """View and respond to enquiry"""
    enquiry = get_object_or_404(ContactEnquiry, id=enquiry_id)

    if request.method == "POST":
        response = request.POST.get("response")
        new_status = request.POST.get("status")

        if response:
            enquiry.admin_response = response
            enquiry.responded_by = request.user

        if new_status in ["pending", "in_progress", "resolved"]:
            enquiry.status = new_status

        enquiry.save()
        messages.success(request, "Enquiry updated successfully.")
        return redirect("custom_admin:enquiry_detail", enquiry_id=enquiry_id)

    context = {
        "title": f"Enquiry from {enquiry.first_name} {enquiry.last_name}",
        "enquiry": enquiry,
    }
    return render(request, "custom_admin/enquiries/detail.html", context)


@login_required
@user_passes_test(is_admin)
def enquiry_delete(request, enquiry_id):
    """Delete an enquiry"""
    enquiry = get_object_or_404(ContactEnquiry, id=enquiry_id)

    if request.method == "POST":
        enquiry.delete()
        messages.success(request, "Enquiry has been deleted.")
        return redirect("custom_admin:enquiry_list")

    context = {
        "title": "Delete Enquiry",
        "enquiry": enquiry,
    }
    return render(request, "custom_admin/enquiries/delete.html", context)


# ==================== DOCUMENT MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def document_list(request):
    """List all documents"""
    documents = Document.objects.select_related("uploaded_by").all()

    # Search
    search = request.GET.get("search")
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | Q(summary__icontains=search)
        )

    documents = documents.order_by("-created_at")

    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Document Management",
        "page_obj": page_obj,
        "search": search,
    }
    return render(request, "custom_admin/documents/list.html", context)


@login_required
@user_passes_test(is_admin)
def document_create(request):
    """Create a new document"""
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(
                request, f"Document '{document.title}' has been uploaded successfully."
            )
            return redirect("custom_admin:document_detail", document_id=document.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentUploadForm()

    context = {
        "title": "Upload Document",
        "form": form,
    }
    return render(request, "custom_admin/documents/create.html", context)


@login_required
@user_passes_test(is_admin)
def document_detail(request, document_id):
    """View document details"""
    document = get_object_or_404(
        Document.objects.select_related("uploaded_by"), id=document_id
    )

    context = {
        "title": document.title or "Document",
        "document": document,
    }
    return render(request, "custom_admin/documents/detail.html", context)


@login_required
@user_passes_test(is_admin)
def document_delete(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id)

    if request.method == "POST":
        title = document.title
        document.delete()
        messages.success(request, f"Document '{title}' has been deleted.")
        return redirect("custom_admin:document_list")

    context = {
        "title": "Delete Document",
        "document": document,
    }
    return render(request, "custom_admin/documents/delete.html", context)


# ==================== AWARENESS MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def awareness_list(request):
    """List all awareness posts and events"""
    awareness_items = Awareness.objects.all()

    # Filtering
    item_type = request.GET.get("type")
    search = request.GET.get("search")

    if item_type == "event":
        awareness_items = awareness_items.filter(is_event=True)
    elif item_type == "post":
        awareness_items = awareness_items.filter(is_event=False)

    if search:
        awareness_items = awareness_items.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    awareness_items = awareness_items.order_by("-created_at")

    # Pagination
    paginator = Paginator(awareness_items, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Awareness Management",
        "page_obj": page_obj,
        "item_type": item_type,
        "search": search,
    }
    return render(request, "custom_admin/awareness/list.html", context)


@login_required
@user_passes_test(is_admin)
def awareness_create(request):
    """Create a new awareness post or event"""
    if request.method == "POST":
        form = AwarenessForm(request.POST, request.FILES)
        if form.is_valid():
            awareness = form.save()
            messages.success(
                request, f"Awareness '{awareness.title}' has been created successfully."
            )
            return redirect("custom_admin:awareness_detail", awareness_id=awareness.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AwarenessForm()

    context = {
        "title": "Create Awareness",
        "form": form,
    }
    return render(request, "custom_admin/awareness/create.html", context)


@login_required
@user_passes_test(is_admin)
def awareness_detail(request, awareness_id):
    """View awareness details"""
    awareness = get_object_or_404(Awareness, id=awareness_id)

    context = {
        "title": awareness.title,
        "awareness": awareness,
    }
    return render(request, "custom_admin/awareness/detail.html", context)


@login_required
@user_passes_test(is_admin)
def awareness_delete(request, awareness_id):
    """Delete an awareness post"""
    awareness = get_object_or_404(Awareness, id=awareness_id)

    if request.method == "POST":
        title = awareness.title
        awareness.delete()
        messages.success(request, f"'{title}' has been deleted.")
        return redirect("custom_admin:awareness_list")

    context = {
        "title": "Delete Awareness",
        "awareness": awareness,
    }
    return render(request, "custom_admin/awareness/delete.html", context)


# ==================== CHAT HISTORY MANAGEMENT ====================


@login_required
@user_passes_test(is_admin)
def chat_history_list(request):
    """List all chat history"""
    chats = ChatHistory.objects.select_related("user").all()

    # Search
    search = request.GET.get("search")
    if search:
        chats = chats.filter(
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(question__icontains=search)
            | Q(answer__icontains=search)
        )

    chats = chats.order_by("-timestamp")

    # Pagination
    paginator = Paginator(chats, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Chat History",
        "page_obj": page_obj,
        "search": search,
    }
    return render(request, "custom_admin/chats/list.html", context)


@login_required
@user_passes_test(is_admin)
def chat_detail(request, chat_id):
    """View chat details"""
    chat = get_object_or_404(ChatHistory, id=chat_id)

    context = {
        "title": f"Chat by {chat.user.username}",
        "chat": chat,
    }
    return render(request, "custom_admin/chats/detail.html", context)


@login_required
@user_passes_test(is_admin)
def chat_delete(request, chat_id):
    """Delete a chat"""
    chat = get_object_or_404(ChatHistory, id=chat_id)

    if request.method == "POST":
        chat.delete()
        messages.success(request, "Chat has been deleted.")
        return redirect("custom_admin:chat_history_list")

    context = {
        "title": "Delete Chat",
        "chat": chat,
    }
    return render(request, "custom_admin/chats/delete.html", context)


# ==================== EXPORT FUNCTIONALITY ====================


@login_required
@user_passes_test(is_admin)
def export_data(request):
    """Export data as CSV"""
    data_type = request.GET.get("type")

    if data_type == "users":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Username",
                "Email",
                "First Name",
                "Last Name",
                "Role",
                "Active",
                "Date Joined",
            ]
        )

        users = Account.objects.all()
        for user in users:
            writer.writerow(
                [
                    user.username,
                    user.email,
                    user.first_name,
                    user.last_name,
                    user.role,
                    user.is_active,
                    user.date_joined,
                ]
            )

    elif data_type == "appointments":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="appointments.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "ID",
                "Villager",
                "Health Worker",
                "Date",
                "Time",
                "Status",
                "Priority",
                "Created",
            ]
        )

        appointments = Appointment.objects.select_related(
            "villager", "healthworker"
        ).all()
        for appt in appointments:
            writer.writerow(
                [
                    appt.id,
                    appt.villager.get_full_name(),
                    appt.healthworker.get_full_name() if appt.healthworker else "N/A",
                    appt.date,
                    appt.time,
                    appt.status,
                    appt.priority,
                    appt.created_at,
                ]
            )

    elif data_type == "enquiries":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="enquiries.csv"'

        writer = csv.writer(response)
        writer.writerow(["Name", "Email", "Phone", "Status", "Created", "Message"])

        enquiries = ContactEnquiry.objects.all()
        for enq in enquiries:
            writer.writerow(
                [
                    f"{enq.first_name} {enq.last_name}",
                    enq.email,
                    enq.phone,
                    enq.status,
                    enq.created_at,
                    enq.message,
                ]
            )

    else:
        return HttpResponse("Invalid export type", status=400)

    return response


# =============================================
# ADMIN PROFILE
# =============================================


@login_required
@user_passes_test(is_admin)
def admin_profile(request):
    """Admin profile page"""
    from accounts.forms import UserProfileUpdateForm
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    user = request.user
    
    if request.method == 'POST':
        # Check which form was submitted
        if 'update_profile' in request.POST:
            user_form = UserProfileUpdateForm(request.POST, instance=user)
            
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('custom_admin:profile')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password changed successfully!')
                return redirect('custom_admin:profile')
            else:
                # Re-initialize user form for display
                user_form = UserProfileUpdateForm(instance=user)
                
                context = {
                    'user_form': user_form,
                    'password_form': password_form,
                    'user': user,
                }
                return render(request, 'custom_admin/profile.html', context)
    else:
        user_form = UserProfileUpdateForm(instance=user)
        password_form = PasswordChangeForm(user=user)
    
    context = {
        'user_form': user_form,
        'password_form': password_form,
        'user': user,
    }
    return render(request, 'custom_admin/profile.html', context)
