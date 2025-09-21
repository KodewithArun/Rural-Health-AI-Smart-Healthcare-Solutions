from django import forms
from .models import Document

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file', 'summary']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter a brief summary (optional)'}),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'txt', 'md']:
                raise forms.ValidationError('Only PDF, DOCX, TXT, and MD files are allowed.')
            
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('File size must be less than 10MB.')
        
        return file

class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'summary']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter a brief summary'}),
        }