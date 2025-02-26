from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path("add_blood_donor/", views.add_blood_donor, name="add_blood_donor"),
    path(
        "store_blood_donor_details/",
        views.store_blood_donor_details,
        name="store_blood_donor_details",
    ),
    path('blood_repo_receptionist/', views.blood_repo_receptionist, name='blood_repo_receptionist'),
    path('check_patient_exists/', views.check_patient_exists, name='check_patient_exists'),
    path('create_patient_account/', views.create_patient_account, name='create_patient_account'),
]