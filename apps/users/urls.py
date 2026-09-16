from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("panel/", views.dashboard, name="dashboard"),
]
