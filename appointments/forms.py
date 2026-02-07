from django import forms
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from .models import Appointment

# Generate 30-minute time slots from 9:00 AM to 5:00 PM
HEALTH_POST_OPEN = time(9, 0)
HEALTH_POST_CLOSE = time(17, 0)


def get_time_slot_choices():
    """Generate time slot choices (9:00 AM to 4:30 PM in 30-min intervals)."""
    slots = []
    current = datetime.combine(date.today(), HEALTH_POST_OPEN)
    end = datetime.combine(date.today(), HEALTH_POST_CLOSE)
    while current < end:
        t = current.time()
        label = current.strftime("%I:%M %p")
        slots.append((t.strftime("%H:%M"), label))
        current += timedelta(minutes=30)
    return slots


TIME_SLOT_CHOICES = [("", "Select a time slot")] + get_time_slot_choices()


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "date",
            "time",
            "reason",
            "healthworker",
            "priority",
            "health_document",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.Select(choices=TIME_SLOT_CHOICES),
            "priority": forms.HiddenInput(),
            "health_document": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.jpg,.jpeg,.png,.doc,.docx"}
            ),
        }

    def clean_health_document(self):
        doc = self.cleaned_data.get("health_document")
        if doc:
            # Max 10 MB
            if doc.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10 MB.")
            # Allowed extensions
            allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
            import os

            ext = os.path.splitext(doc.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
                )
        return doc

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["healthworker"].queryset = self.fields[
                "healthworker"
            ].queryset.filter(role="health_worker", health_profile__availability=True)
        self.fields["date"].widget.attrs["min"] = date.today().isoformat()

        # Set default priority value for hidden field
        if not self.instance.pk:
            self.fields["priority"].initial = "normal"

    def clean_date(self):
        appointment_date = self.cleaned_data.get("date")
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("You cannot book appointments in the past.")
        return appointment_date

    def clean_time(self):
        appointment_time = self.cleaned_data.get("time")
        if appointment_time:
            if (
                appointment_time < HEALTH_POST_OPEN
                or appointment_time >= HEALTH_POST_CLOSE
            ):
                raise forms.ValidationError(
                    "Please select a time between 9:00 AM and 5:00 PM (health post operating hours)."
                )
        return appointment_time

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("date")
        appointment_time = cleaned_data.get("time")
        healthworker = cleaned_data.get("healthworker")

        if appointment_date and appointment_time:
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            appointment_datetime = timezone.make_aware(appointment_datetime)

            if appointment_datetime < timezone.now() + timedelta(hours=1):
                raise forms.ValidationError(
                    "Appointments must be booked at least 1 hour in advance."
                )

            # Check for conflicting appointments (same health worker, same date, same time)
            if healthworker:
                conflict = Appointment.objects.filter(
                    healthworker=healthworker,
                    date=appointment_date,
                    time=appointment_time,
                    status__in=["pending", "approved"],
                )
                # Exclude current instance if editing
                if self.instance.pk:
                    conflict = conflict.exclude(pk=self.instance.pk)

                if conflict.exists():
                    hw_name = f"Dr. {healthworker.first_name} {healthworker.last_name}"
                    time_str = appointment_time.strftime("%I:%M %p")
                    raise forms.ValidationError(
                        f"{hw_name} already has an appointment at {time_str} on "
                        f"{appointment_date.strftime('%b %d, %Y')}. Please choose a different time slot."
                    )

        return cleaned_data


class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            "date",
            "time",
            "reason",
            "healthworker",
            "priority",
            "status",
            "note",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.Select(choices=TIME_SLOT_CHOICES),
            "note": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add notes or remarks here..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["healthworker"].queryset = self.fields[
                "healthworker"
            ].queryset.filter(role="health_worker")

        # Add helpful labels for priority field
        self.fields["priority"].help_text = (
            "AI-classified priority. Can be manually adjusted if needed."
        )

    def clean_date(self):
        appointment_date = self.cleaned_data.get("date")
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appointment_date

    def clean_time(self):
        appointment_time = self.cleaned_data.get("time")
        if appointment_time:
            if (
                appointment_time < HEALTH_POST_OPEN
                or appointment_time >= HEALTH_POST_CLOSE
            ):
                raise forms.ValidationError(
                    "Please select a time between 9:00 AM and 5:00 PM (health post operating hours)."
                )
        return appointment_time

    def clean_reason(self):
        reason = self.cleaned_data.get("reason")
        if not reason or not reason.strip():
            raise forms.ValidationError("Reason is required.")
        reason = reason.strip()
        if len(reason) < 5:
            raise forms.ValidationError("Reason must be at least 5 characters long.")
        return reason

    def clean_note(self):
        note = self.cleaned_data.get("note")
        if note:
            note = note.strip()
        return note or ""

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("date")
        appointment_time = cleaned_data.get("time")
        status = cleaned_data.get("status")
        healthworker = cleaned_data.get("healthworker")

        if (
            appointment_date
            and appointment_time
            and status not in ["completed", "cancelled"]
        ):
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            appointment_datetime = timezone.make_aware(appointment_datetime)

            if appointment_datetime < timezone.now():
                raise forms.ValidationError(
                    "Cannot set a pending/approved appointment to a past date and time."
                )

            # Check for conflicting appointments
            if healthworker:
                conflict = Appointment.objects.filter(
                    healthworker=healthworker,
                    date=appointment_date,
                    time=appointment_time,
                    status__in=["pending", "approved"],
                )
                if self.instance.pk:
                    conflict = conflict.exclude(pk=self.instance.pk)

                if conflict.exists():
                    hw_name = f"Dr. {healthworker.first_name} {healthworker.last_name}"
                    time_str = appointment_time.strftime("%I:%M %p")
                    raise forms.ValidationError(
                        f"{hw_name} already has an appointment at {time_str} on "
                        f"{appointment_date.strftime('%b %d, %Y')}. Please choose a different time slot."
                    )

        return cleaned_data
