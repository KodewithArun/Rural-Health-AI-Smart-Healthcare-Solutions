# from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(ModelAdmin):
    list_display = (
        'villager', 'healthworker', 'date', 'time', 
        'status', 'token', 'created_at'
    )
    list_filter = ('status', 'date', 'healthworker')
    search_fields = (
        'villager__username', 'villager__email',
        'healthworker__username', 'healthworker__email',
        'reason', 'token'
    )
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'villager', 'healthworker', 'date', 'time', 'reason'
            )
        }),
        ('Status & Notes', {
            'fields': ('status', 'note')
        }),
        ('System Information', {
            'fields': ('token', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Optimize queries by selecting related objects
        return super().get_queryset(request).select_related(
            'villager', 'healthworker'
        )
    
    def get_readonly_fields(self, request, obj=None):
        # Make token and created_at readonly in both add and change forms
        return self.readonly_fields