from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("signup_success/", views.signup_success, name="signup_success"),
    path("login_success/", views.login_success, name="login_success"),
    path("check_username/", views.check_username, name="check_username"),
    path("forgot_password/", views.forgot_password_view, name="forgot_password"),
]
