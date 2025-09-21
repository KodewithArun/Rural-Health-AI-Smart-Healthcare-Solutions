from django import forms

class ChatForm(forms.Form):
    message = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Type your message here...',
                'id': 'chat-input',
                'autocomplete': 'off'
            }
        )
    )