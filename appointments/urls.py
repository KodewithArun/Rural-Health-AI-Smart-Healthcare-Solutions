from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('create/', views.appointment_create, name='create'),
    path('<int:pk>/update/', views.appointment_update, name='update'),
    path('<int:pk>/delete/', views.appointment_delete, name='delete'),
    path('<int:pk>/cancel/', views.villager_cancel_appointment, name='cancel'),
]
