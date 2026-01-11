from django import forms
from .models import ContactEnquiry


class ContactEnquiryForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ["first_name", "last_name", "email", "phone", "message"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Enter your first name",
                    "pattern": "^[a-zA-Z ]+$",
                    "title": "Only alphabets and spaces allowed",
                    "required": "required",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Enter your last name",
                    "pattern": "^[a-zA-Z ]+$",
                    "title": "Only alphabets and spaces allowed",
                    "required": "required",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "example@gmail.com",
                    "required": "required",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "98XXXXXXXX or 97XXXXXXXX",
                    "pattern": "^(98|97)[0-9]{8}$",
                    "title": "Phone must start with 98 or 97 and be 10 digits",
                    "maxlength": "10",
                    "required": "required",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    "placeholder": "Tell us how we can help you...",
                    "rows": 4,
                    "required": "required",
                    "minlength": "10",
                }
            ),
        }

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

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and not email.endswith("@gmail.com"):
            raise forms.ValidationError("Email must be a Gmail address (@gmail.com)")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must contain only digits.")
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be exactly 10 digits.")
            if not (phone.startswith("98") or phone.startswith("97")):
                raise forms.ValidationError("Phone number must start with 98 or 97.")
        return phone

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if message and len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        return message


class AdminResponseForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ["status", "admin_response"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "admin_response": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Type your response to the enquiry...",
                }
            ),
        }
