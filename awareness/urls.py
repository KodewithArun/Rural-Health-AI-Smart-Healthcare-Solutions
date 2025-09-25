from django.urls import path
from . import views

urlpatterns = [
    path('', views.awareness_list, name='awareness_list'),
    path('<int:pk>/', views.awareness_detail, name='awareness_detail'),
]