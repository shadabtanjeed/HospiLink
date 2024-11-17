# django_project/patient/views.py
from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
from django.core.paginator import Paginator


def index(request):
    # Your existing index view code
    return render(request, "patient_page.html")


def fetch_doctors():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                username, 
                public.get_name(username) AS name, 
                phone_no, 
                visiting_days, 
                visiting_time_start, 
                visiting_time_end, 
                specialization, 
                fee, 
                degrees
            FROM doctors
        """
        )
        doctors = cursor.fetchall()
        doctor_list = []
        for doctor in doctors:
            # doctor[3] is visiting_days
            visiting_days = doctor[3] if doctor[3] else []
            # Ensure visiting_days is a list
            if isinstance(visiting_days, list):
                visiting_days = [day.capitalize() for day in visiting_days]
            else:
                # Handle as string
                visiting_days = (
                    visiting_days.replace("{", "").replace("}", "").split(",")
                )
                visiting_days = [day.strip().capitalize() for day in visiting_days]

            # doctor[8] is degrees
            degrees = doctor[8] if doctor[8] else []
            if isinstance(degrees, list):
                degrees = [degree.strip() for degree in degrees]
            else:
                degrees = degrees.replace("{", "").replace("}", "").split(",")
                degrees = [degree.strip() for degree in degrees]

            visiting_time_start = doctor[4].strftime("%I:%M %p") if doctor[4] else "N/A"
            visiting_time_end = doctor[5].strftime("%I:%M %p") if doctor[5] else "N/A"

            doctor_list.append(
                {
                    "username": doctor[0],
                    "name": doctor[1],
                    "phone_no": doctor[2],
                    "visiting_days": visiting_days,
                    "visiting_time_start": visiting_time_start,
                    "visiting_time_end": visiting_time_end,
                    "specialization": doctor[6],
                    "fee": doctor[7],
                    "degrees": degrees,
                }
            )
    return doctor_list


def search_doctor(request):
    doctors = fetch_doctors()

    # Set up pagination: 5 doctors per page
    paginator = Paginator(doctors, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj}
    return render(request, "search_doctor.html", context)


def profile_picture(request, username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_profile_pic(%s)", [username])
        profile_picture = cursor.fetchone()[0]
    return HttpResponse(profile_picture, content_type="image/png")
