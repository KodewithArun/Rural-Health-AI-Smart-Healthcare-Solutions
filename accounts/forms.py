# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Account as User, HealthWorkerProfile


class VillagerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "example@gmail.com"}
        ),
    )
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "98XXXXXXXX or 97XXXXXXXX",
                "pattern": "^(98|97)[0-9]{8}$",
                "title": "Phone must start with 98 or 97 and be 10 digits",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
                "pattern": "^[a-zA-Z ]+$",
                "title": "Only alphabets and spaces allowed",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
                "pattern": "^[a-zA-Z ]+$",
                "title": "Only alphabets and spaces allowed",
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "pattern": "^[a-zA-Z0-9@.+_-]+$",
                "title": "Username can contain letters, numbers, and @/./+/-/_ only",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "phone_number",
            "first_name",
            "last_name",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if not email.endswith("@gmail.com"):
                raise forms.ValidationError(
                    "Email must be a Gmail address (@gmail.com)"
                )
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must contain only digits.")
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be exactly 10 digits.")
            if not (phone.startswith("98") or phone.startswith("97")):
                raise forms.ValidationError("Phone number must start with 98 or 97.")
            if User.objects.filter(phone_number=phone).exists():
                raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            if (
                not username.replace("_", "")
                .replace("-", "")
                .replace(".", "")
                .replace("@", "")
                .replace("+", "")
                .isalnum()
            ):
                raise forms.ValidationError(
                    "Username can only contain letters, numbers, and @/./+/-/_ characters."
                )
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if first_name and not first_name.replace(" ", "").isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if last_name and not last_name.replace(" ", "").isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return last_name

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = "villager"
        user.phone_number = self.cleaned_data.get("phone_number", "")
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
        return user


class HealthWorkerCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "example@gmail.com"}
        ),
    )
    phone_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "98XXXXXXXX or 97XXXXXXXX",
                "pattern": "^(98|97)[0-9]{8}$",
                "title": "Phone must start with 98 or 97 and be 10 digits",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
                "pattern": "^[a-zA-Z ]+$",
                "title": "Only alphabets and spaces allowed",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
                "pattern": "^[a-zA-Z ]+$",
                "title": "Only alphabets and spaces allowed",
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username (letters, numbers, only)",
                "pattern": "^[a-zA-Z0-9]+$",
                "title": "Username can contain letters and numbers only",
            }
        ),
    )

    SPECIALIZATION_CHOICES = [
        ("general_practice", "General Practice / Family Medicine"),
        ("internal_medicine", "Internal Medicine"),
        ("pediatrics", "Pediatrics"),
        ("cardiology", "Cardiology"),
        ("dermatology", "Dermatology"),
        ("orthopedics", "Orthopedics"),
        ("neurology", "Neurology"),
        ("psychiatry", "Psychiatry"),
        ("radiology", "Radiology"),
        ("anesthesiology", "Anesthesiology"),
        ("obstetrics_gynecology", "Obstetrics & Gynecology"),
        ("emergency_medicine", "Emergency Medicine"),
        ("gastroenterology", "Gastroenterology"),
        ("urology", "Urology"),
        ("ophthalmology", "Ophthalmology"),
        ("oncology", "Oncology"),
        ("endocrinology", "Endocrinology"),
        ("public_health", "Public Health"),
        ("pathology", "Pathology"),
        ("neonatology", "Neonatology"),
    ]
    specialization = forms.ChoiceField(
        choices=SPECIALIZATION_CHOICES,
        required=True,
        label="Specialization",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    QUALIFICATION_CHOICES = [
        ("mbbs", "MBBS (Bachelor of Medicine, Bachelor of Surgery)"),
        ("md", "MD (Doctor of Medicine)"),
        ("ms", "MS (Master of Surgery)"),
        ("dm", "DM (Doctorate of Medicine – Super/Specialty)"),
        ("mch", "MCh (Master of Chirurgiae – Surgical Super/Specialty)"),
        ("fcps", "FCPS (Fellow of College of Physicians & Surgeons)"),
        ("facs", "FACS (Fellow of the American College of Surgeons)"),
        ("frcp", "FRCP (Fellow of the Royal College of Physicians)"),
        ("mrch", "MRCS (Member of Royal College of Surgeons)"),
        ("phd", "PhD (Doctor of Philosophy – Medical Research)"),
        ("diploma", "Diploma in Medical/Clinical Specialization"),
    ]
    qualification = forms.ChoiceField(
        choices=QUALIFICATION_CHOICES,
        required=True,
        label="Qualification",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=25,
        required=True,
        label="Years of Experience",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "0-25",
                "min": "0",
                "max": "25",
            }
        ),
    )
    availability = forms.BooleanField(
        required=False,
        initial=True,
        label="Available for Appointments",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "phone_number",
            "first_name",
            "last_name",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if not email.endswith("@gmail.com"):
                raise forms.ValidationError(
                    "Email must be a Gmail address (@gmail.com)"
                )
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")
        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must contain only digits.")
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be exactly 10 digits.")
            if not (phone.startswith("98") or phone.startswith("97")):
                raise forms.ValidationError("Phone number must start with 98 or 97.")
            if User.objects.filter(phone_number=phone).exists():
                raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            if (
                not username.replace("_", "")
                .replace("-", "")
                .replace(".", "")
                .replace("@", "")
                .replace("+", "")
                .isalnum()
            ):
                raise forms.ValidationError(
                    "Username can only contain letters, numbers, and @/./+/-/_ characters."
                )
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if first_name and not first_name.replace(" ", "").isalpha():
            raise forms.ValidationError("First name must contain only letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if last_name and not last_name.replace(" ", "").isalpha():
            raise forms.ValidationError("Last name must contain only letters.")
        return last_name

    def clean_experience_years(self):
        experience = self.cleaned_data.get("experience_years")
        if experience is not None:
            if experience < 0:
                raise forms.ValidationError("Experience years cannot be negative.")
            if experience > 50:
                raise forms.ValidationError("Experience years cannot exceed 50.")
        return experience

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "health_worker"
        if commit:
            user.save()
            HealthWorkerProfile.objects.create(
                user=user,
                specialization=self.cleaned_data["specialization"],
                qualification=self.cleaned_data.get("qualification", ""),
                experience_years=self.cleaned_data.get("experience_years") or 0,
                availability=self.cleaned_data.get("availability", True),
            )
        return user


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone_number")
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "First Name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Last Name"}
            ),
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone Number"}
            ),
        }


class HealthWorkerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = HealthWorkerProfile
        fields = ("specialization", "qualification", "experience_years", "availability")
        widgets = {
            "specialization": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Specialization"}
            ),
            "qualification": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Qualification"}
            ),
            "experience_years": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Years of Experience"}
            ),
            "availability": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password",
            }
        ),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enter new password"}
        ),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm new password"}
        ),
    )
