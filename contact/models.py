from django.db import models
from accounts.models import Account as User


class ContactEnquiry(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_enquiries', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_responses')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Enquiry'
        verbose_name_plural = 'Contact Enquiries'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.created_at.strftime('%Y-%m-%d')}"
