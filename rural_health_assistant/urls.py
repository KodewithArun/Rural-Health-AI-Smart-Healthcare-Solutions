from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .admin_dashboard import dashboard_view

# Customize admin site
admin.site.site_header = "Rural Health AI Support System"
admin.site.site_title = "Health Admin"
admin.site.index_title = "Dashboard & Analytics"

# Override admin index view
admin.site.index = dashboard_view

# Custom error handlers
handler400 = 'rural_health_assistant.views.custom_400'
handler403 = 'rural_health_assistant.views.custom_403'
handler404 = 'rural_health_assistant.views.custom_404'
handler500 = 'rural_health_assistant.views.custom_500'

urlpatterns = [
    # Custom Admin Panel - accessible at /admin/
    path('admin/', include('rural_health_assistant.admin_urls', namespace='custom_admin')),
    
    # Django Default Admin (Keep for superadmin - use /django-admin/)
    path('django-admin/dashboard/', dashboard_view, name='admin_dashboard'),
    path('django-admin/', admin.site.urls),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('documents/', include('documents.urls')),
    path('chat/', include('chat.urls')),
    path('awareness/', include('awareness.urls')),
    path('appointments/', include('appointments.urls', namespace='appointments')),
    path('contact/', include('contact.urls', namespace='contact')),
    
    # Main Pages
    path('', views.home, name='home'),
    path('emergency-alert/', views.emergency_alert, name='emergency_alert'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
