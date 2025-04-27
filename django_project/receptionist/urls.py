from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path("add_blood_donor/", views.add_blood_donor, name="add_blood_donor"),
    path("store_blood_donor_details/", views.store_blood_donor_details, name="store_blood_donor_details",),
    path('blood_repo_receptionist/', views.blood_repo_receptionist, name='blood_repo_receptionist'),
    path('check_patient_exists/', views.check_patient_exists, name='check_patient_exists'),
    path('create_patient_account/', views.create_patient_account, name='create_patient_account'),
    path('receptionist_search_doctor/', views.receptionist_search_doctor, name='receptionist_search_doctor'),
    path("book_appointment/<str:doctor_username>/", views.receptionist_book_appointment, name="receptionist_book_appointment"),
    path('patient_appointments/', views.patient_appointments, name='patient_appointments'),
    path('api/upcoming_appointments_for_patient/', views.upcoming_appointments_for_patient, name='upcoming_appointments_for_patient'),
    path('cancel_appointment/', views.cancel_appointment, name='cancel_appointment'),
    path('modify_appointment/<str:doctor_username>/<str:appointment_date>/', views.receptionist_modify_appointment, name='receptionist_modify_appointment'),
]