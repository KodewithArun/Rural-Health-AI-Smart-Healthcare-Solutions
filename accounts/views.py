# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import Account as User
from .forms import VillagerRegistrationForm, HealthWorkerCreationForm


# -------------------------------
# Villager Registration (Public)
def villager_register(request):
    if request.user.is_authenticated:
        if request.user.is_villager:
            return redirect('home')
        elif request.user.is_health_worker:
            return redirect('appointments:list')
        else:
            return redirect('admin:index')

    if request.method == 'POST':
        form = VillagerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('accounts:login')
    else:
        form = VillagerRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


# -------------------------------
# Admin-only Health Worker Creation
@user_passes_test(lambda u: u.is_authenticated and u.is_admin_role, login_url='accounts:login')
def create_healthworker(request):
    if request.method == "POST":
        form = HealthWorkerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Health Worker account created successfully.")
            return redirect('admin:index')  # Redirect to Django admin after creation
    else:
        form = HealthWorkerCreationForm()
    return render(request, 'accounts/create_healthworker.html', {'form': form})


# -------------------------------
# Login
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_villager:
            return redirect('home')
        elif request.user.is_health_worker:
            return redirect('appointments:list')
        else:
            return redirect('admin:index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Note: Your custom user uses email as USERNAME_FIELD, so authenticate with email
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            if user.is_villager:
                return redirect('home')
            elif user.is_health_worker:
                return redirect('appointments:list')
            else:
                return redirect('admin:index')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html')


# -------------------------------
# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')