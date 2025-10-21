# from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import ChatHistory

@admin.register(ChatHistory)
class ChatHistoryAdmin(ModelAdmin):
    list_display = ("user", "get_question_preview", "get_answer_preview", "timestamp")
    search_fields = ("user__username", "question", "answer")
    list_filter = ("timestamp",)
    readonly_fields = ("user", "question", "answer", "timestamp")
    
    def get_question_preview(self, obj):
        return obj.get_question_preview(100)
    get_question_preview.short_description = "Question"
    
    def get_answer_preview(self, obj):
        return obj.get_answer_preview(100)
    get_answer_preview.short_description = "Answer"
    

    
        
    