from datetime import date, time
import json
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

    try:
        with connection.cursor() as cursor:
            # First, get the server's timezone-aware current date
            cursor.execute("SET timezone = 'Asia/Dhaka';")  # Set to your timezone
            cursor.execute("""
                SELECT 
                    a.*,
                    CASE 
                        WHEN p.prescription_id IS NOT NULL THEN true 
                        ELSE false 
                    END as has_prescription,
                    CASE 
                        WHEN DATE(a.appointment_date) = CURRENT_DATE THEN true
                        ELSE false
                    END as is_today,
                    a.appointment_date::date = CURRENT_DATE as appointment_is_today
                FROM show_upcoming_appointments(%s, %s) a
                LEFT JOIN prescriptions p ON a.appointment_id = p.appointment_id
            """, [username, user_type])
            
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Process the data
            for item in data:
                if isinstance(item["appointment_date"], date):
                    item["appointment_date"] = item["appointment_date"].strftime("%Y-%m-%d")
                if isinstance(item["appointment_time"], time):
                    item["appointment_time"] = item["appointment_time"].strftime("%H:%M:%S")
                
                # Use the direct boolean comparison from the database
                item["is_today"] = item["appointment_is_today"]
                
                patient_username = item["with_user"]
                if patient_username:
                    cursor.execute("SELECT public.get_name(%s)", [patient_username])
                    patient_name = cursor.fetchone()[0]
                    item["patient_name"] = patient_name

            return JsonResponse(data, safe=False)
    except Exception as e:
        import traceback
        print(f"Error in fetch_upcoming_appointments:")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


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

    print(f"Username: {username}, User Type: {user_type}")

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

        # Fetch doctor details (join doctors and users tables to get the actual name)
        doctor_username = appointment[
            2
        ]  # Assuming the doctor's username is the third column
        cursor.execute(
            """
            SELECT u.name, d.degrees
            FROM doctors d
            INNER JOIN users u ON d.username = u.username
            WHERE d.username = %s
        """,
            [doctor_username],
        )
        doctor = cursor.fetchone()

        # Convert degrees array to a string (e.g., "M.B.B.S., M.S.(Ortho)")
        doctor_name = doctor[0]
        doctor_degrees = ", ".join(doctor[1])  # Join the array elements with a comma

        # Fetch patient details
        patient_username = appointment[
            1
        ]  # Assuming the patient's username is the second column
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
            "appointment_date": appointment[3].strftime("%Y-%m-%d"),
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
            diagnosis = data.get(
                "diagnosis"
            )  # String with diagnoses separated by newline
            medication = data.get(
                "medication"
            )  # String with medications separated by newline
            additional_notes = data.get("additional_notes")

            if not all(
                [appointment_id, prescribed_by, prescribed_to, diagnosis, medication]
            ):
                return JsonResponse(
                    {"success": False, "message": "Missing required fields"}, status=400
                )

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
        return JsonResponse(
            {"success": False, "message": "Invalid request method"}, status=405
        )


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


@require_POST
@csrf_exempt
def approve_discharge(request):
    """API endpoint to approve a discharge request."""
    try:
        data = json.loads(request.body)
        discharge_id = data.get("discharge_id")
        admission_id = data.get("admission_id")

        if not discharge_id or not admission_id:
            return JsonResponse(
                {"success": False, "message": "Missing discharge_id or admission_id"},
                status=400,
            )

        # Use uppercase 'APPROVED' to match the check constraint
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE discharge_requests 
                SET status = 'APPROVED' 
                WHERE discharge_id = %s
                """,
                [discharge_id],
            )

        # Then call the existing discharge_patient function to handle actual discharge
        with connection.cursor() as cursor:
            cursor.execute("SELECT public.discharge_patient(%s)", [admission_id])

        return JsonResponse({"success": True})
    except Exception as e:
        import traceback

        print(f"Error in approve_discharge: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_POST
@csrf_exempt
def reject_discharge(request):
    """API endpoint to reject a discharge request."""
    try:
        data = json.loads(request.body)
        discharge_id = data.get("discharge_id")

        if not discharge_id:
            return JsonResponse(
                {"success": False, "message": "Missing discharge_id"}, status=400
            )

        # Use uppercase 'REJECTED' to match the check constraint
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE discharge_requests 
                SET status = 'REJECTED' 
                WHERE discharge_id = %s
                """,
                [discharge_id],
            )

        return JsonResponse({"success": True})
    except Exception as e:
        import traceback

        print(f"Error in reject_discharge: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_prescription(request, appointment_id):
    """API endpoint to get prescription details for a specific appointment."""
    try:
        with connection.cursor() as cursor:
            # Get prescription details
            cursor.execute(
                """
                SELECT 
                    p.diagnosis,
                    p.medication,
                    p.additional_notes,
                    p.prescription_date,
                    d.degrees,
                    (SELECT name FROM users WHERE username = p.prescribed_by) as doctor_name,
                    (SELECT name FROM users WHERE username = p.prescribed_to) as patient_name
                FROM prescriptions p
                JOIN doctors d ON p.prescribed_by = d.username
                WHERE p.appointment_id = %s
            """,
                [appointment_id],
            )

            result = cursor.fetchone()

            if result:
                prescription_data = {
                    "diagnosis": result[0],
                    "medication": result[1],
                    "additional_notes": result[2],
                    "created_at": result[3].strftime("%Y-%m-%d"),
                    "doctor_degrees": ", ".join(result[4]) if result[4] else "",
                    "prescribed_by": result[5],
                    "prescribed_to": result[6],
                }
                return JsonResponse(prescription_data)
            else:
                return JsonResponse({"error": "No prescription found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@csrf_exempt
def discharge_patient(request):
    """API endpoint to directly discharge a patient."""
    try:
        data = json.loads(request.body)
        admission_id = data.get("admission_id")

        if not admission_id:
            return JsonResponse(
                {"success": False, "message": "Missing admission_id"}, status=400
            )

        # First, get the bed_id from the admission
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT bed_id FROM admissions WHERE admission_id = %s", [admission_id]
            )
            result = cursor.fetchone()
            if not result:
                return JsonResponse(
                    {"success": False, "message": "Admission not found"}, status=404
                )
            bed_id = result[0]

        # Call the discharge_patient function (which will update admissions and clear patient info)
        with connection.cursor() as cursor:
            cursor.execute("SELECT public.discharge_patient(%s)", [admission_id])
            result = cursor.fetchone()[0]  # Get the boolean result

        # Now set bed to maintenance status with current timestamp
        if result:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE beds 
                    SET status = 'Maintenance', 
                        maintenance_start = CURRENT_TIMESTAMP 
                    WHERE bed_id = %s
                    """,
                    [bed_id],
                )
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"success": False, "message": "Failed to discharge patient"}, status=500
            )
    except Exception as e:
        import traceback

        print(f"Error in discharge_patient: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_POST
@csrf_exempt
def update_maintenance_beds(request):
    """API endpoint to check and update maintenance beds that have been in maintenance for over 15 seconds."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE beds
                SET status = 'Vacant', 
                    maintenance_start = NULL
                WHERE status = 'Maintenance'
                AND maintenance_start < (CURRENT_TIMESTAMP - INTERVAL '15 seconds')
                """
            )
        return JsonResponse({"success": True})
    except Exception as e:
        import traceback

        print(f"Error updating maintenance beds: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)
