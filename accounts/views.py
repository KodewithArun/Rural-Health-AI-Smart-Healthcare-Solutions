# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Account as User, HealthWorkerProfile
from .forms import (
    VillagerRegistrationForm,
    HealthWorkerCreationForm,
    UserProfileUpdateForm,
    HealthWorkerProfileUpdateForm,
    CustomPasswordChangeForm,
)


# -------------------------------
# Villager Registration (Public)
def villager_register(request):
    if request.user.is_authenticated:
        if request.user.is_villager:
            return redirect("home")
        elif request.user.is_health_worker:
            return redirect("appointments:list")
        elif request.user.is_superadmin or request.user.role == "admin":
            return redirect("custom_admin:dashboard")
        else:
            return redirect("custom_admin:dashboard")

    if request.method == "POST":
        form = VillagerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Account created successfully. You can now log in."
            )
            return redirect("accounts:login")
    else:
        form = VillagerRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


# -------------------------------
# Admin-only Health Worker Creation
@user_passes_test(
    lambda u: u.is_authenticated and u.is_admin_role, login_url="accounts:login"
)
def create_healthworker(request):
    if request.method == "POST":
        form = HealthWorkerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Health Worker account created successfully.")
            return redirect(
                "custom_admin:user_list"
            )  # Redirect to custom admin user list
    else:
        form = HealthWorkerCreationForm()
    return render(request, "accounts/create_healthworker.html", {"form": form})


# -------------------------------
# Login
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_villager:
            return redirect("home")
        elif request.user.is_health_worker:
            return redirect("accounts:health_worker_dashboard")
        elif request.user.is_superadmin or request.user.role == "admin":
            return redirect("custom_admin:dashboard")
        else:
            return redirect("custom_admin:dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        # Note: Your custom user uses email as USERNAME_FIELD, so authenticate with email
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            if user.is_villager:
                return redirect("home")
            elif user.is_health_worker:
                return redirect("accounts:health_worker_dashboard")
            elif user.is_superadmin or user.role == "admin":
                return redirect("custom_admin:dashboard")
            else:
                return redirect("home")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html")


# -------------------------------
# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("accounts:login")


# -------------------------------
# Profile Update
@login_required
def profile_view(request):
    user = request.user

    # Redirect admins to admin panel profile
    if user.is_superadmin or user.role == "admin":
        return redirect("custom_admin:profile")

    health_profile = None

    # Get health worker profile if user is a health worker
    if user.is_health_worker:
        health_profile = HealthWorkerProfile.objects.filter(user=user).first()

    if request.method == "POST":
        # Check which form was submitted
        if "update_profile" in request.POST:
            user_form = UserProfileUpdateForm(request.POST, instance=user)
            health_form = None

            if user.is_health_worker and health_profile:
                health_form = HealthWorkerProfileUpdateForm(
                    request.POST, instance=health_profile
                )

            if user_form.is_valid():
                if health_form:
                    if health_form.is_valid():
                        user_form.save()
                        health_form.save()
                        messages.success(request, "Profile updated successfully!")
                        return redirect("accounts:profile")
                else:
                    user_form.save()
                    messages.success(request, "Profile updated successfully!")
                    return redirect("accounts:profile")

        elif "change_password" in request.POST:
            password_form = CustomPasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(
                    request, password_form.user
                )  # Keep user logged in
                messages.success(request, "Password changed successfully!")
                return redirect("accounts:profile")
            else:
                # Re-initialize other forms for display
                user_form = UserProfileUpdateForm(instance=user)
                health_form = None
                if user.is_health_worker and health_profile:
                    health_form = HealthWorkerProfileUpdateForm(instance=health_profile)

                context = {
                    "user_form": user_form,
                    "health_form": health_form,
                    "password_form": password_form,
                    "user": user,
                    "health_profile": health_profile,
                }
                return render(request, "accounts/profile.html", context)
    else:
        user_form = UserProfileUpdateForm(instance=user)
        health_form = None
        password_form = CustomPasswordChangeForm(user=user)

        if user.is_health_worker and health_profile:
            health_form = HealthWorkerProfileUpdateForm(instance=health_profile)

    context = {
        "user_form": user_form,
        "health_form": health_form,
        "password_form": password_form,
        "user": user,
        "health_profile": health_profile,
    }
    return render(request, "accounts/profile.html", context)


# -------------------------------
# Health Worker Dashboard
@login_required
@user_passes_test(
    lambda u: u.is_authenticated and u.is_health_worker, login_url="accounts:login"
)
def health_worker_dashboard(request):
    from appointments.models import Appointment
    from chat.models import ChatHistory

    user = request.user
    health_profile = HealthWorkerProfile.objects.filter(user=user).first()

    # Get today's date
    today = timezone.now().date()

    # Appointment statistics
    total_appointments = Appointment.objects.filter(healthworker=user).count()
    pending_appointments = Appointment.objects.filter(
        healthworker=user, status="pending"
    ).count()
    approved_appointments = Appointment.objects.filter(
        healthworker=user, status="approved"
    ).count()
    completed_appointments = Appointment.objects.filter(
        healthworker=user, status="completed"
    ).count()
    cancelled_appointments = Appointment.objects.filter(
        healthworker=user, status="cancelled"
    ).count()

    # Today's appointments
    todays_appointments = Appointment.objects.filter(
        healthworker=user, date=today
    ).order_by("time")

    # Upcoming appointments (next 7 days)
    upcoming_appointments = Appointment.objects.filter(
        healthworker=user,
        date__gte=today,
        date__lte=today + timedelta(days=7),
        status__in=["pending", "approved"],
    ).order_by("date", "time")[:5]

    # Recent appointments
    recent_appointments = Appointment.objects.filter(healthworker=user).order_by(
        "-date", "-time"
    )[:5]

    # Get total villagers who have appointments with this health worker
    total_villagers = (
        Appointment.objects.filter(healthworker=user)
        .values("villager")
        .distinct()
        .count()
    )

    # Weekly appointment trend (last 7 days)
    weekly_appointments = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Appointment.objects.filter(healthworker=user, date=day).count()
        weekly_appointments.append({"date": day.strftime("%a"), "count": count})

    # Status distribution for chart
    status_distribution = {
        "pending": pending_appointments,
        "approved": approved_appointments,
        "completed": completed_appointments,
        "cancelled": cancelled_appointments,
    }

    context = {
        "user": user,
        "health_profile": health_profile,
        "current_date": today,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "approved_appointments": approved_appointments,
        "completed_appointments": completed_appointments,
        "cancelled_appointments": cancelled_appointments,
        "todays_appointments": todays_appointments,
        "upcoming_appointments": upcoming_appointments,
        "recent_appointments": recent_appointments,
        "total_villagers": total_villagers,
        "weekly_appointments": weekly_appointments,
        "status_distribution": status_distribution,
    }
    return render(request, "accounts/health_worker_dashboard.html", context)
