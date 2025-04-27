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
]
