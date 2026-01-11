from django import forms
from .models import Awareness


class AwarenessForm(forms.ModelForm):
    class Meta:
        model = Awareness
        fields = ["title", "description", "photo", "pdf", "event_date", "is_event"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                    "placeholder": "Enter awareness title",
                    "required": "required",
                    "minlength": "5",
                    "maxlength": "200",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                    "rows": 5,
                    "placeholder": "Enter description",
                    "required": "required",
                    "minlength": "20",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                    "accept": "image/jpeg,image/jpg,image/png,image/gif",
                }
            ),
            "pdf": forms.FileInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                    "accept": "application/pdf",
                }
            ),
            "event_date": forms.DateInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500",
                    "type": "date",
                }
            ),
            "is_event": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if title:
            if len(title) < 5:
                raise forms.ValidationError("Title must be at least 5 characters long.")
            if len(title) > 200:
                raise forms.ValidationError("Title must not exceed 200 characters.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if description and len(description) < 20:
            raise forms.ValidationError(
                "Description must be at least 20 characters long."
            )
        return description

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo:
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image size must be less than 5MB.")
            ext = photo.name.split(".")[-1].lower()
            if ext not in ["jpg", "jpeg", "png", "gif"]:
                raise forms.ValidationError(
                    "Only JPG, JPEG, PNG, and GIF images are allowed."
                )
        return photo

    def clean_pdf(self):
        pdf = self.cleaned_data.get("pdf")
        if pdf:
            if pdf.size > 10 * 1024 * 1024:
                raise forms.ValidationError("PDF size must be less than 10MB.")
            ext = pdf.name.split(".")[-1].lower()
            if ext != "pdf":
                raise forms.ValidationError("Only PDF files are allowed.")
        return pdf
