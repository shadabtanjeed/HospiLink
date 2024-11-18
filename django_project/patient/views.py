# django_project/patient/views.py
from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.urls import reverse


def index(request):
    username = request.session.get("patient_username", "")

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_name(%s)", [username])
        name = cursor.fetchone()[0]

    return render(request, "patient_page.html", {"username": username, "name": name})


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
    paginator = Paginator(doctors, 3)  # Change to 3 as per your requirement
    page_number = request.GET.get("page")

    if not page_number:
        # Redirect to the same view with ?page=1 if 'page' is not present
        return redirect(f"{reverse('search_doctor')}?page=1")

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_obj = paginator.get_page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        page_obj = paginator.get_page(paginator.num_pages)

    context = {"page_obj": page_obj}
    return render(request, "search_doctor.html", context)


def profile_picture(request, username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_profile_pic(%s)", [username])
        profile_picture = cursor.fetchone()[0]
    return HttpResponse(profile_picture, content_type="image/png")
