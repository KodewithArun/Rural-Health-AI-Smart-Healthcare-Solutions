from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documents/', views.document_list, name='document_list'),
    path('upload/', views.upload_document, name='upload_document'),
    path('update/<int:pk>/', views.update_document, name='update_document'),
    path('delete/<int:pk>/', views.delete_document, name='delete_document'),
    path('stats/', views.document_stats, name='document_stats'),
]