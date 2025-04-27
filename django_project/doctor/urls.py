from django.urls import path
from . import views  # Corrected import path

urlpatterns = [
    path("", views.index, name="index"),
    path("index/", views.index, name="index"),
    path(
        "api/upcoming_appointments/",
        views.fetch_upcoming_appointments,
        name="fetch_upcoming_appointments",
    ),
    path(
        "previous_appointments/",
        views.previous_appointments,
        name="previous_appointments",
    ),
    path(
        "api/previous_appointments/",
        views.fetch_previous_appointments,
        name="fetch_previous_appointments",
    ),
    path(
        "attend_appointment/<int:appointment_id>/",
        views.attend_appointment,
        name="attend_appointment",
    ),
    path("ward_management/", views.ward_management_page, name="ward_management_page"),
    path("api/assigned_beds/", views.get_assigned_beds, name="get_assigned_beds"),
    path(
        "api/patient_notes/<int:admission_id>/",
        views.get_patient_notes,
        name="get_patient_notes",
    ),
    path("api/add_doctor_note/", views.add_doctor_note, name="add_doctor_note"),
]
