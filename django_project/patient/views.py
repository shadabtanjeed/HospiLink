# django_project/patient/views.py
from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
import json
from datetime import datetime

def index(request):
    # Your existing index view code
    return render(request, "patient_page.html")


def search_doctor(request):
    # Your logic to handle the search doctor page
    return render(request, "search_doctor.html")


def fetch_doctors():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT username, phone_no, visiting_days, visiting_time_start, visiting_time_end, specialization, fee, degrees
            FROM doctors
        """
        )
        doctors = cursor.fetchall()
        doctor_list = []
        for doctor in doctors:
            try:
                visiting_time_start = (
                    doctor[3].strftime("%I:%M %p") if doctor[3] else "N/A"
                )
                visiting_time_end = (
                    doctor[4].strftime("%I:%M %p") if doctor[4] else "N/A"
                )
            except AttributeError:
                # In case the time is already a string or different format
                visiting_time_start = str(doctor[3])
                visiting_time_end = str(doctor[4])

            visiting_days = doctor[2].replace("{", "").replace("}", "").split(",")
            visiting_days = [day.capitalize() for day in visiting_days]
            degrees = (
                doctor[7]
                if isinstance(doctor[7], list)
                else doctor[7].replace("{", "").replace("}", "").split(",")
            )
            doctor_list.append(
                {
                    "username": doctor[0],
                    "phone_no": doctor[1],
                    "visiting_days": visiting_days,
                    "visiting_time_start": visiting_time_start,
                    "visiting_time_end": visiting_time_end,
                    "specialization": doctor[5],
                    "fee": doctor[6],
                    "degrees": degrees,
                }
            )
    return doctor_list


def search_doctor(request):
    doctors = fetch_doctors()
    return render(request, "search_doctor.html", {"doctors": doctors})


def profile_picture(request, username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_profile_pic(%s)", [username])
        profile_picture = cursor.fetchone()[0]
    return HttpResponse(profile_picture, content_type="image/png")

def blood_repo(request):
    return render(request, 'blood_repo_patient.html')


def fetch_blood_repo_data(request):
    blood_group = request.GET.get('blood_group', '')
    with connection.cursor() as cursor:
        if blood_group:
            cursor.execute("SELECT * FROM search_donor(%s)", [blood_group])
        else:
            cursor.execute("SELECT * FROM search_donor('*')")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        for item in data:
            if isinstance(item['last_donation'], datetime):
                item['last_donation'] = item['last_donation'].strftime('%Y-%m-%d %H:%M:%S')
    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")