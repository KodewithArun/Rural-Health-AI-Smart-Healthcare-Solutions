from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.villager_register, name="register"),
    path("create-healthworker/", views.create_healthworker, name="create_healthworker"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
