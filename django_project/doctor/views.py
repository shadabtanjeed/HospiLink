from datetime import date, time
import json
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_POST


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

    return render(
        request, "previous_appointments.html", {"username": username, "name": name}
    )


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
    return (
        today.year
        - date_of_birth.year
        - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
    )


def attend_appointment(request, appointment_id):
    with connection.cursor() as cursor:
        # Fetch appointment details
        cursor.execute(
            "SELECT * FROM appointments WHERE appointment_id = %s", [appointment_id]
        )
        appointment = cursor.fetchone()

        # Fetch patient details (join users and patients tables)
        patient_username = appointment[1]  # patient_username is the second column
        cursor.execute(
            """
            SELECT u.name, p.phone_no, p.blood_group, p.complexities, p.date_of_birth, p.gender
            FROM patients p
            INNER JOIN users u ON p.username = u.username
            WHERE p.username = %s
        """,
            [patient_username],
        )
        patient = cursor.fetchone()

        # Fetch previous prescriptions
        cursor.execute(
            "SELECT * FROM prescriptions WHERE prescribed_to = %s", [patient_username]
        )
        prescriptions = cursor.fetchall()

    # Calculate age
    age = calculate_age(patient[4])  # Assuming date_of_birth is the 5th column

    # Prepare context with patient details
    context = {
        "appointment": appointment,
        "patient": {
            "name": patient[0],
            "phone_no": patient[1],
            "blood_group": patient[2],
            "complexities": patient[3],
            "date_of_birth": patient[4],
            "gender": patient[5],
            "age": age,
            "appointment_date": appointment[3].strftime("%Y-%m-%d"),
        },
        "prescriptions": prescriptions,
    }
    return render(request, "attend_app.html", context)


def ward_management_page(request):

    return render(request, "doctor_ward_management.html")


def get_assigned_beds(request):
    """API endpoint to get beds assigned to the logged-in doctor."""
    doctor_username = request.session.get("login_form_data", {}).get("username")

    if not doctor_username:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        with connection.cursor() as cursor:
            # Call the database function instead of running raw SQL
            cursor.execute(
                "SELECT * FROM public.get_doctor_assigned_beds(%s)", [doctor_username]
            )
            columns = [col[0] for col in cursor.description]
            beds = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get nurse names
            for bed in beds:
                if bed.get("nurse_username"):
                    cursor.execute(
                        "SELECT public.get_name(%s)", [bed["nurse_username"]]
                    )
                    bed["nurse_name"] = cursor.fetchone()[0]
                else:
                    bed["nurse_name"] = "Not assigned"

                # Convert datetime objects to string for JSON serialization
                if bed.get("check_in_date"):
                    bed["check_in_date"] = bed["check_in_date"].isoformat()
                if bed.get("check_out_date"):
                    bed["check_out_date"] = bed["check_out_date"].isoformat()

            return JsonResponse(beds, safe=False)
    except Exception as e:
        import traceback

        print(f"Error in get_assigned_beds: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


def get_patient_notes(request, admission_id):
    """API endpoint to get notes for a specific patient admission."""
    try:
        with connection.cursor() as cursor:
            # Call the PostgreSQL function to get patient notes
            cursor.execute(
                "SELECT * FROM public.get_patient_notes(%s)",
                [admission_id],
            )
            columns = [col[0] for col in cursor.description]
            notes = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Convert timestamp objects to strings
            for note in notes:
                if note.get("note_timestamp"):
                    note["timestamp"] = note["note_timestamp"].isoformat()
                    del note[
                        "note_timestamp"
                    ]  # Use standardized field name for frontend

                # Rename note to text for frontend consistency
                note["text"] = note["note"]
                del note["note"]

                # Add author_type if needed (you can add default if not present in function result)
                if "author_type" not in note:
                    note["author_type"] = "doctor"

        return JsonResponse({"success": True, "notes": notes})
    except Exception as e:
        import traceback

        print(f"Error in get_patient_notes: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_POST
def add_doctor_note(request):
    """API endpoint to add a doctor note for a patient admission."""
    try:
        data = json.loads(request.body)
        admission_id = data.get("admission_id")
        note = data.get("note")
        doctor_username = request.session.get("login_form_data", {}).get("username")

        if not all([admission_id, note, doctor_username]):
            return JsonResponse(
                {"success": False, "message": "Missing required data"}, status=400
            )

        with connection.cursor() as cursor:
            # Call the SQL function to add a doctor note
            cursor.execute(
                "SELECT public.add_doctor_bed_note(%s, %s)",
                [admission_id, note],
            )

        return JsonResponse({"success": True})
    except Exception as e:
        import traceback

        print(f"Error in add_doctor_note: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def discharge_requests_page(request):
    """Render the discharge requests page."""
    doctor_username = request.session.get("login_form_data", {}).get("username")

    if not doctor_username:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    return render(request, "doctor_discharge_requests.html")


def get_discharge_requests(request):
    """API endpoint to get discharge requests for the logged-in doctor."""
    doctor_username = request.session.get("login_form_data", {}).get("username")

    if not doctor_username:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        with connection.cursor() as cursor:
            # Call the database function
            cursor.execute(
                "SELECT * FROM public.get_discharge_requests(%s)", [doctor_username]
            )
            columns = [col[0] for col in cursor.description]
            discharge_requests = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return JsonResponse(discharge_requests, safe=False)
    except Exception as e:
        import traceback

        print(f"Error in get_discharge_requests: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
