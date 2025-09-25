from django.db import models

class Awareness(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to='awareness_photos/')
    pdf = models.FileField(upload_to='awareness_pdfs/', blank=True, null=True)
    event_date = models.DateField(blank=True, null=True)
    is_event = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title