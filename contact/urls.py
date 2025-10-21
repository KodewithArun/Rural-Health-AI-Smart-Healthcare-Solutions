from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    # User views only - admins use the default admin panel
    path('my-enquiries/', views.my_enquiries, name='my_enquiries'),
]
