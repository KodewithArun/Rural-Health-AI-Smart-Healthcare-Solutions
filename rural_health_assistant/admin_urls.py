# rural_health_assistant/admin_urls.py
from django.urls import path
from . import admin_views

app_name = "custom_admin"

urlpatterns = [
    # Dashboard
    path("", admin_views.admin_dashboard, name="dashboard"),
    # User Management
    path("users/", admin_views.user_list, name="user_list"),
    path(
        "users/create-healthworker/",
        admin_views.user_create_healthworker,
        name="user_create_healthworker",
    ),
    path("users/<int:user_id>/", admin_views.user_detail, name="user_detail"),
    path(
        "users/<int:user_id>/toggle/",
        admin_views.user_toggle_status,
        name="user_toggle_status",
    ),
    path("users/<int:user_id>/delete/", admin_views.user_delete, name="user_delete"),
    # Appointment Management
    path("appointments/", admin_views.appointment_list, name="appointment_list"),
    path(
        "appointments/<int:appointment_id>/",
        admin_views.appointment_detail,
        name="appointment_detail",
    ),
    path(
        "appointments/<int:appointment_id>/status/",
        admin_views.appointment_update_status,
        name="appointment_update_status",
    ),
    path(
        "appointments/<int:appointment_id>/assign/",
        admin_views.appointment_assign,
        name="appointment_assign",
    ),
    path(
        "appointments/<int:appointment_id>/delete/",
        admin_views.appointment_delete,
        name="appointment_delete",
    ),
    # Enquiry Management
    path("enquiries/", admin_views.enquiry_list, name="enquiry_list"),
    path(
        "enquiries/<int:enquiry_id>/", admin_views.enquiry_detail, name="enquiry_detail"
    ),
    path(
        "enquiries/<int:enquiry_id>/delete/",
        admin_views.enquiry_delete,
        name="enquiry_delete",
    ),
    # Document Management
    path("documents/", admin_views.document_list, name="document_list"),
    path("documents/create/", admin_views.document_create, name="document_create"),
    path(
        "documents/<int:document_id>/",
        admin_views.document_detail,
        name="document_detail",
    ),
    path(
        "documents/<int:document_id>/delete/",
        admin_views.document_delete,
        name="document_delete",
    ),
    # Awareness Management
    path("awareness/", admin_views.awareness_list, name="awareness_list"),
    path("awareness/create/", admin_views.awareness_create, name="awareness_create"),
    path(
        "awareness/<int:awareness_id>/",
        admin_views.awareness_detail,
        name="awareness_detail",
    ),
    path(
        "awareness/<int:awareness_id>/delete/",
        admin_views.awareness_delete,
        name="awareness_delete",
    ),
    # Chat History Management
    path("chats/", admin_views.chat_history_list, name="chat_history_list"),
    path("chats/<int:chat_id>/", admin_views.chat_detail, name="chat_detail"),
    path("chats/<int:chat_id>/delete/", admin_views.chat_delete, name="chat_delete"),
    # Admin Profile
    path("profile/", admin_views.admin_profile, name="profile"),
    # Export
    path("export/", admin_views.export_data, name="export_data"),
]
