from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import User
from .forms import CustomUserCreationForm

def register_view(request):
    
    # Redirect already logged-in users
    if request.user.is_authenticated:
        if hasattr(request.user, 'is_villager') and request.user.is_villager:
            return redirect('home')  # URL name for villager home
        else:
            return redirect('admin:index')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    # Redirect already logged-in users
    if request.user.is_authenticated:
        if hasattr(request.user, 'is_villager') and request.user.is_villager:
            return redirect('home')  # URL name for villager home
        else:
            return redirect('admin:index')

    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # username OR email
        password = request.POST.get('password')
        user = None

        # Try login with username
        user = authenticate(request, username=identifier, password=password)

        # If not found, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        # Authenticate and redirect by role
        if user is not None:
            login(request, user)
            if hasattr(user, 'is_villager') and user.is_villager:
                return redirect('home')
            else:
                return redirect('admin:index')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')