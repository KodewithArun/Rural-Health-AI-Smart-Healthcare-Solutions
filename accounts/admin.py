# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, HealthWorkerProfile, HealthWorker


# Inline for Health Worker Profile
class HealthWorkerProfileInline(admin.StackedInline):
    model = HealthWorkerProfile
    can_delete = False
    verbose_name_plural = "Health Worker Details"
    extra = 0  # Don't show extra empty forms

    def has_add_permission(self, request, obj=None):
        # Allow adding profile only if obj is a health worker (or being created as one)
        return True  # We'll control visibility via parent

    def has_change_permission(self, request, obj=None):
        return True


# Admin for general users (non-health-workers)
class AccountAdmin(UserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "username", "first_name", "last_name")
    readonly_fields = ("date_joined", "last_login")
    ordering = ("-date_joined",)
    filter_horizontal = ()

    fieldsets = (
        (None, {"fields": ("email", "username", "first_name", "last_name", "phone_number", "password", "role")}),
        ("Permissions", {"fields": ("is_admin", "is_staff", "is_active", "is_superadmin")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "phone_number", "role", "password1", "password2"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(role='health_worker')


# Admin for Health Workers (proxy model)
class HealthWorkerAdmin(UserAdmin):
    inlines = [HealthWorkerProfileInline]
    list_display = ("email", "first_name", "last_name", "get_specialization", "get_availability", "is_active")
    list_filter = ("health_profile__specialization", "health_profile__availability", "is_active")
    search_fields = ("email", "first_name", "last_name", "health_profile__specialization")
    readonly_fields = ("date_joined", "last_login")
    ordering = ("-date_joined",)
    filter_horizontal = ()

    fieldsets = (
        (None, {"fields": ("email", "username", "first_name", "last_name", "phone_number", "password")}),
        ("Permissions", {"fields": ("is_admin", "is_staff", "is_active", "is_superadmin")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "phone_number", "password1", "password2"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='health_worker')

    def get_specialization(self, obj):
        return obj.health_profile.specialization if hasattr(obj, 'health_profile') else '-'
    get_specialization.short_description = 'Specialization'
    get_specialization.admin_order_field = 'health_profile__specialization'

    def get_availability(self, obj):
        return obj.health_profile.availability if hasattr(obj, 'health_profile') else False
    get_availability.boolean = True
    get_availability.short_description = 'Available'

    def save_model(self, request, obj, form, change):
        obj.role = 'health_worker'
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        # Ensure role is set to health_worker
        form = super().get_form(request, obj, **kwargs)
        return form

    def get_inline_instances(self, request, obj=None):
        # Show inline even when adding new health worker
        return [inline(self.model, self.admin_site) for inline in self.inlines]


# Register both
admin.site.register(Account, AccountAdmin)
admin.site.register(HealthWorker, HealthWorkerAdmin)