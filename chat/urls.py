from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('send-message/', views.send_message, name='send_message'),
    path('chat-history/', views.chat_history, name='chat_history'),
    path('delete-chat/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('clear-chat-history/', views.clear_chat_history, name='clear_chat_history'),
    path('export-chat-history/', views.export_chat_history, name='export_chat_history'),
    path('villager-history/', views.villager_history, name='villager_history'),
    path('export-villager-history/', views.export_villager_history, name='export_villager_history'),
]