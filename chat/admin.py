from django.contrib import admin
from .models import ChatHistory

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "timestamp")
    search_fields = ("user__username", "question")
    list_filter = ("timestamp",)
