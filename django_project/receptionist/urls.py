# django_project/patient/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path('add_blood_donor/', views.add_blood_donor, name='add_blood_donor'),
]
