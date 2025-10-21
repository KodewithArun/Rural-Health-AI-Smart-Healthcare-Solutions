from django import forms
from django.utils import timezone
from datetime import datetime, date, timedelta
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'reason', 'healthworker']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['healthworker'].queryset = \
                self.fields['healthworker'].queryset.filter(
                    role='health_worker',
                    health_profile__availability=True
                )
        self.fields['date'].widget.attrs['min'] = date.today().isoformat()

    def clean_date(self):
        appointment_date = self.cleaned_data.get('date')
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("You cannot book appointments in the past.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('date')
        appointment_time = cleaned_data.get('time')
        
        if appointment_date and appointment_time:
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            appointment_datetime = timezone.make_aware(appointment_datetime)

            if appointment_datetime < timezone.now() + timedelta(hours=1):
                raise forms.ValidationError("Appointments must be booked at least 1 hour in advance.")
        return cleaned_data

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'reason', 'healthworker', 'status', 'note']  # added note
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add notes or remarks here...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['healthworker'].queryset = \
                self.fields['healthworker'].queryset.filter(role='health_worker')

