from datetime import date, time
import json
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def index(request):
    username = request.session.get("doctor_username", "")

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_name(%s)", [username])
        name = cursor.fetchone()[0]

    return render(request, "doctor_page.html", {"username": username, "name": name})

def fetch_upcoming_appointments(request):
    username = request.session.get("login_form_data", {}).get("username")
    user_type = request.session.get("login_form_data", {}).get("user_type")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM show_upcoming_appointments(%s, %s)", [username, user_type]
        )
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert date and time objects to strings
        for item in data:
            if isinstance(item["appointment_date"], date):
                item["appointment_date"] = item["appointment_date"].strftime("%Y-%m-%d")
            if isinstance(item["appointment_time"], time):
                item["appointment_time"] = item["appointment_time"].strftime("%H:%M:%S")

            patient_username = item["with_user"]
            cursor.execute("SELECT public.get_name(%s)", [patient_username])
            patient_name = cursor.fetchone()[0]
            item["patient_name"] = patient_name

    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")



def previous_appointments(request):
    username = request.session.get("doctor_username", "")

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_name(%s)", [username])
        name = cursor.fetchone()[0]

    return render(request, 'previous_appointments.html', {"username": username, "name": name})


def fetch_previous_appointments(request):
    username = request.session.get("login_form_data", {}).get("username")
    user_type = request.session.get("login_form_data", {}).get("user_type")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM show_past_appointments(%s, %s)", [username, user_type]
        )
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Convert date and time objects to strings
        for item in data:
            if isinstance(item["appointment_date"], date):
                item["appointment_date"] = item["appointment_date"].strftime("%Y-%m-%d")
            if isinstance(item["appointment_time"], time):
                item["appointment_time"] = item["appointment_time"].strftime("%H:%M:%S")

            patient_username = item["related_user"]
            cursor.execute("SELECT public.get_name(%s)", [patient_username])
            patient_name = cursor.fetchone()[0]
            item["patient_name"] = patient_name

    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")

