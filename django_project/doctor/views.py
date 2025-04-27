from datetime import date, time
import json
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from datetime import date

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

def calculate_age(date_of_birth):
    today = date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def attend_appointment(request, appointment_id):
    with connection.cursor() as cursor:
        # Fetch appointment details
        cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s", [appointment_id])
        appointment = cursor.fetchone()

        # Fetch doctor details (join doctors and users tables to get the actual name)
        doctor_username = appointment[2]  # Assuming the doctor's username is the third column
        cursor.execute("""
            SELECT u.name, d.degrees
            FROM doctors d
            INNER JOIN users u ON d.username = u.username
            WHERE d.username = %s
        """, [doctor_username])
        doctor = cursor.fetchone()

        # Convert degrees array to a string (e.g., "M.B.B.S., M.S.(Ortho)")
        doctor_name = doctor[0]
        doctor_degrees = ", ".join(doctor[1])  # Join the array elements with a comma

        # Fetch patient details
        patient_username = appointment[1]  # Assuming the patient's username is the second column
        cursor.execute("""
            SELECT u.name, p.phone_no, p.blood_group, p.complexities, p.date_of_birth, p.gender
            FROM patients p
            INNER JOIN users u ON p.username = u.username
            WHERE p.username = %s
        """, [patient_username])
        patient = cursor.fetchone()

        # Fetch previous prescriptions
        cursor.execute("SELECT * FROM prescriptions WHERE prescribed_to = %s", [patient_username])
        prescriptions = cursor.fetchall()

    # Calculate age
    age = calculate_age(patient[4])  # Assuming date_of_birth is the 5th column

    # Prepare context with doctor, patient, and appointment details
    context = {
        "appointment": appointment,
        "doctor": {
            "name": doctor_name,
            "degrees": doctor_degrees,
        },
        "patient": {
            "name": patient[0],
            "phone_no": patient[1],
            "blood_group": patient[2],
            "complexities": patient[3],
            "date_of_birth": patient[4],
            "gender": patient[5],
            "age": age,
            "appointment_date": appointment[3].strftime('%Y-%m-%d'),
        },
        "prescriptions": prescriptions,
    }
    return render(request, "attend_app.html", context)

@csrf_exempt
def save_prescription(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appointment_id = data.get("appointment_id")
            prescribed_by = data.get("prescribed_by")
            prescribed_to = data.get("prescribed_to")
            diagnosis = data.get("diagnosis")  # String with diagnoses separated by newline
            medication = data.get("medication")  # String with medications separated by newline
            additional_notes = data.get("additional_notes")

            if not all([appointment_id, prescribed_by, prescribed_to, diagnosis, medication]):
                return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.prescriptions (
                        appointment_id, prescribed_by, prescribed_to, 
                        diagnosis, medication, additional_notes
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [
                        appointment_id,
                        prescribed_by,
                        prescribed_to,
                        diagnosis,
                        medication,
                        additional_notes,
                    ],
                )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)