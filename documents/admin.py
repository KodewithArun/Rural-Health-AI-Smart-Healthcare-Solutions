# from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ("title", "uploaded_by", "created_at", "updated_at")
    search_fields = ("title", "uploaded_by__username")

    def get_form(self, request, obj=None, **kwargs):
        """Filter uploaded_by to only show admin users."""
        form = super().get_form(request, obj, **kwargs)
        if 'uploaded_by' in form.base_fields:
            # ✅ Use your custom field (is_admin instead of is_superuser)
            form.base_fields['uploaded_by'].queryset = (
                form.base_fields['uploaded_by'].queryset.filter(is_admin=True)
            )
            # Optional: auto-select the first admin user as default
            admin_user = form.base_fields['uploaded_by'].queryset.first()
            if admin_user:
                form.base_fields['uploaded_by'].initial = admin_user
        return form

    def save_model(self, request, obj, form, change):
        """Auto-assign the current user if not set."""
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        obj.save()
