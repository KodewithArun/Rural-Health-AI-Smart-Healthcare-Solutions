# from django.contrib import admin
from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
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

    def delete_model(self, request, obj):
        """Override to ensure model's delete() is called (triggers vector cleanup)."""
        obj.delete()  # This calls the model's delete() method with vector cleanup

    def delete_queryset(self, request, queryset):
        """Override bulk delete to call delete() on each object individually."""
        # Don't use queryset.delete() - it bypasses model delete()
        for obj in queryset:
            obj.delete()  # Calls model's delete() for each, triggering vector cleanup
