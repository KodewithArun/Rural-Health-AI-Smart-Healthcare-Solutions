from django import forms
from .models import ContactEnquiry


class ContactEnquiryForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ['first_name', 'last_name', 'email', 'phone', 'message']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter your phone number'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Tell us how we can help you...',
                'rows': 4
            }),
        }


class AdminResponseForm(forms.ModelForm):
    class Meta:
        model = ContactEnquiry
        fields = ['status', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'admin_response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your response to the enquiry...'
            }),
        }
