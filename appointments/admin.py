# from django.contrib import admin
from django.contrib import admin
from django import forms
from .models import Appointment
from accounts.models import Account as User


class AppointmentAdminForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter healthworker to show only users with health_worker role
        if 'healthworker' in self.fields:
            self.fields['healthworker'].queryset = User.objects.filter(role='health_worker')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
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
    readonly_fields = ('villager', 'token', 'created_at')
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