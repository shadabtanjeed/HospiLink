# django_project/patient/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path("search_doctor/", views.search_doctor, name="search_doctor"),
    path(
        "profile_picture/<str:username>/", views.profile_picture, name="profile_picture"
    ),
    path("blood_repo/", views.blood_repo, name="blood_repo"),
    path("api/blood_repo/", views.fetch_blood_repo_data, name="fetch_blood_repo_data"),
    path(
        "api/upcoming_appointments/",
        views.fetch_upcoming_appointments,
        name="fetch_upcoming_appointments",
    ),
]
