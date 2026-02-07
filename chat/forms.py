from django import forms


class ChatForm(forms.Form):
    message = forms.CharField(
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Type your message here...",
                "id": "chat-input",
                "autocomplete": "off",
                "maxlength": "2000",
            }
        ),
    )

    def clean_message(self):
        message = self.cleaned_data.get("message")
        if not message or not message.strip():
            raise forms.ValidationError("Message cannot be empty.")
        message = message.strip()
        if len(message) > 2000:
            raise forms.ValidationError("Message must be under 2000 characters.")
        return message
