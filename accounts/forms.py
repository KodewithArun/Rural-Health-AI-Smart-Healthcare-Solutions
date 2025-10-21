# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Account as User, HealthWorkerProfile


class VillagerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'phone_number', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'villager'
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class HealthWorkerCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    specialization = forms.CharField(max_length=100, label="Specialization")
    qualification = forms.CharField(max_length=200, required=False, label="Qualification")
    experience_years = forms.IntegerField(
        min_value=0, 
        required=False, 
        initial=0,
        label="Years of Experience"
    )
    availability = forms.BooleanField(
        required=False, 
        initial=True,
        label="Available for Appointments"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2',
                  'phone_number', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'health_worker'
        if commit:
            user.save()
            HealthWorkerProfile.objects.create(
                user=user,
                specialization=self.cleaned_data['specialization'],
                qualification=self.cleaned_data.get('qualification', ''),
                experience_years=self.cleaned_data.get('experience_years') or 0,
                availability=self.cleaned_data.get('availability', True)
            )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone_number')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }


class HealthWorkerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = HealthWorkerProfile
        fields = ('specialization', 'qualification', 'experience_years', 'availability')
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specialization'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualification'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of Experience'}),
            'availability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )