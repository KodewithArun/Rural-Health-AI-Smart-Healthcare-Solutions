from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('villager', 'Villager'),
        ('health_worker', 'Health Worker'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='villager')
    
    def __str__(self):
        return self.username
    
    @property
    def is_villager(self):
        return self.role == 'villager'
    
    @property
    def is_health_worker(self):
        return self.role == 'health_worker'