from django.db import models
from django.conf import settings
import uuid


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("critical", "Critical"),
        ("medium", "Medium"),
        ("normal", "Normal"),
    ]

    villager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments"
    )
    healthworker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_appointments",
    )
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="normal"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    note = models.TextField(blank=True)
    health_document = models.FileField(
        upload_to="appointment_health_docs/",
        blank=True,
        null=True,
        help_text="Optional: Upload your background health document (PDF, images, etc.)",
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.villager.username} on {self.date}"

    class Meta:
        # Don't use default ordering - priority queue handles sorting
        ordering = []
