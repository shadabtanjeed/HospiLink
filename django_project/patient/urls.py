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
]
