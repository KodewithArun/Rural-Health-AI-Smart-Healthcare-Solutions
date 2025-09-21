from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_by", "created_at", "updated_at")
    search_fields = ("title", "uploaded_by__username")
