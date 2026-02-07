from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file", "summary"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter document title",
                    "required": "required",
                    "minlength": "3",
                    "maxlength": "255",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "required": "required",
                    "accept": ".pdf,.docx,.txt,.md",
                }
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter a brief summary",
                    "required": "required",
                    "minlength": "10",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if title:
            if len(title) < 3:
                raise forms.ValidationError("Title must be at least 3 characters long.")
            if len(title) > 255:
                raise forms.ValidationError("Title must not exceed 255 characters.")
        return title

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            # Check file extension
            ext = file.name.split(".")[-1].lower()
            if ext not in ["pdf", "docx", "txt", "md"]:
                raise forms.ValidationError(
                    "Only PDF, DOCX, TXT, and MD files are allowed."
                )

            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("File size must be less than 10MB.")
        return file

    def clean_summary(self):
        summary = self.cleaned_data.get("summary")
        if summary and len(summary) < 10:
            raise forms.ValidationError("Summary must be at least 10 characters long.")
        return summary


class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "summary"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter document title",
                    "minlength": "3",
                    "maxlength": "255",
                }
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter a brief summary",
                    "minlength": "10",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if not title or not title.strip():
            raise forms.ValidationError("Title is required.")
        title = title.strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        if len(title) > 255:
            raise forms.ValidationError("Title must not exceed 255 characters.")
        return title

    def clean_summary(self):
        summary = self.cleaned_data.get("summary")
        if summary and len(summary.strip()) < 10:
            raise forms.ValidationError("Summary must be at least 10 characters long.")
        return summary.strip() if summary else summary
