# django_project/patient/views.py
from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
import json
from datetime import datetime
from datetime import date, time
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import traceback


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
                degrees,
                gender
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

            # Corrected time formatting to 24-hour format
            visiting_time_start = doctor[4].strftime("%H:%M") if doctor[4] else None
            visiting_time_end = doctor[5].strftime("%H:%M") if doctor[5] else None

            # Ensure gender is appended correctly
            gender = doctor[9].capitalize() if doctor[9] else None

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
                    "gender": gender,
                }
            )
    return doctor_list


def search_doctor(request):
    doctors = fetch_doctors()  # Get all doctors
    context = {"doctors": doctors}  # Send complete list
    return render(request, "search_doctor.html", context)


def profile_picture(request, username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_profile_pic(%s)", [username])
        profile_picture = cursor.fetchone()[0]
    return HttpResponse(profile_picture, content_type="image/png")


def book_appointment(request, doctor_username):
    if request.method == "POST":
        booking_date = request.POST.get("booking_date")
        patient_username = request.session.get("patient_username")

        try:
            with connection.cursor() as cursor:
                # Call the schedule_appointment function
                cursor.execute(
                    """
                    SELECT public.schedule_appointment(%s, %s, %s)
                    """,
                    [patient_username, doctor_username, booking_date],
                )
                # Fetch the appointment time
                cursor.execute(
                    """
                    SELECT appointment_time
                    FROM appointments
                    WHERE patient_username = %s
                      AND doctor_username = %s
                      AND appointment_date = %s
                    """,
                    [patient_username, doctor_username, booking_date],
                )
                appointment_time = cursor.fetchone()[0]

            return JsonResponse(
                {
                    "success": True,
                    "appointment_time": appointment_time.strftime("%H:%M"),
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    else:
        # Fetch doctor information
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, public.get_name(username) AS name, phone_no,
                       visiting_days, visiting_time_start, visiting_time_end,
                       specialization, fee, degrees
                FROM doctors
                WHERE username = %s
                """,
                [doctor_username],
            )
            doctor = cursor.fetchone()

        if doctor:
            # Process doctor data
            visiting_days = doctor[3]
            if isinstance(visiting_days, str):
                visiting_days = visiting_days.strip("{}").split(",")
                visiting_days = [day.capitalize() for day in visiting_days]
            degrees = doctor[8]
            if isinstance(degrees, str):
                degrees = degrees.strip("{}").split(",")

            doctor_info = {
                "username": doctor[0],
                "name": doctor[1],
                "phone_no": doctor[2],
                "visiting_days": visiting_days,
                "visiting_time_start": doctor[4],
                "visiting_time_end": doctor[5],
                "specialization": doctor[6],
                "fee": doctor[7],
                "degrees": degrees,
            }

            # Prepare date range for the next 10 days
            today = timezone.now().date()
            end_date = today + timedelta(days=10)
            date_range = [today + timedelta(days=x) for x in range(0, 11)]

            context = {
                "doctor": doctor_info,
                "date_range": date_range,
                "today": today,
                "end_date": end_date,
            }

            return render(request, "book_appointment.html", context)
        else:
            # Handle case when doctor is not found
            return HttpResponse("Doctor not found.")


def blood_repo(request):
    return render(request, "blood_repo_patient.html")


def fetch_blood_repo_data(request):
    blood_group = request.GET.get("blood_group", "")
    with connection.cursor() as cursor:
        if blood_group:
            cursor.execute("SELECT * FROM search_donor(%s)", [blood_group])
        else:
            cursor.execute("SELECT * FROM search_donor('*')")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        for item in data:
            if isinstance(item["last_donation"], datetime):
                item["last_donation"] = item["last_donation"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")


# django_project/patient/views.py


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

            doctor_username = item["with_user"]
            cursor.execute("SELECT public.get_name(%s)", [doctor_username])

            doctor_name = cursor.fetchone()[0]

            item["doctor_name"] = doctor_name

    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")


def blood_repo_receptionist(request):
    return render(request, "blood_repo_receptionist.html")


# In patient/views.py


def modify_appointment(request, doctor_username, appointment_date):
    if request.method == "POST":
        new_date = request.POST.get("booking_date")
        patient_username = request.session.get("patient_username")

        try:
            with connection.cursor() as cursor:
                # Call the reschedule_appointment function
                cursor.execute(
                    """
                    SELECT public.reschedule_appointment(%s, %s, %s, %s)
                    """,
                    [patient_username, doctor_username, appointment_date, new_date],
                )

                # Fetch the new appointment time
                cursor.execute(
                    """
                    SELECT appointment_time
                    FROM appointments
                    WHERE patient_username = %s
                      AND doctor_username = %s
                      AND appointment_date = %s
                    """,
                    [patient_username, doctor_username, new_date],
                )
                new_appointment_time = cursor.fetchone()[0]

            return JsonResponse(
                {
                    "success": True,
                    "new_date": new_date,
                    "new_time": new_appointment_time.strftime("%H:%M"),
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    else:
        # Fetch doctor information
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, public.get_name(username) AS name, phone_no,
                       visiting_days, visiting_time_start, visiting_time_end,
                       specialization, fee, degrees
                FROM doctors
                WHERE username = %s
                """,
                [doctor_username],
            )
            doctor = cursor.fetchone()

        if doctor:
            # Process doctor data
            visiting_days = doctor[3]
            if isinstance(visiting_days, str):
                visiting_days = visiting_days.strip("{}").split(",")
                visiting_days = [day.capitalize() for day in visiting_days]
            degrees = doctor[8]
            if isinstance(degrees, str):
                degrees = degrees.strip("{}").split(",")

            doctor_info = {
                "username": doctor[0],
                "name": doctor[1],
                "phone_no": doctor[2],
                "visiting_days": visiting_days,
                "visiting_time_start": doctor[4],
                "visiting_time_end": doctor[5],
                "specialization": doctor[6],
                "fee": doctor[7],
                "degrees": degrees,
            }

            # Prepare date range for the next 10 days
            today = timezone.now().date()
            end_date = today + timedelta(days=10)
            date_range = [today + timedelta(days=x) for x in range(0, 11)]

            context = {
                "doctor": doctor_info,
                "date_range": date_range,
                "today": today,
                "end_date": end_date,
                "current_appointment_date": appointment_date,
            }

            return render(request, "modify_appointment.html", context)
        else:
            # Handle case when doctor is not found
            return HttpResponse("Doctor not found.")


@require_POST
def cancel_appointment(request):
    try:
        data = json.loads(request.body)
        doctor_username = data.get("doctor_username")
        appointment_date = data.get("appointment_date")
        patient_username = request.session.get(
            "patient_username"
        ) or request.session.get("login_form_data", {}).get("username")

        if not all([doctor_username, appointment_date, patient_username]):
            return JsonResponse(
                {"success": False, "message": "Missing required data"}, status=400
            )

        with connection.cursor() as cursor:
            # Call the cancel_appointment function
            cursor.execute(
                """
                SELECT public.cancel_appointment(%s, %s, %s)
                """,
                [patient_username, doctor_username, appointment_date],
            )

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def bed_admission(request):
    """Render the bed admission page."""
    return render(request, "patient_bed_admission.html")


def search_beds(request):
    """API endpoint to search for available beds."""
    ward_type = request.GET.get("ward_type", "")
    bed_type = request.GET.get("bed_type", "")

    if not ward_type:
        return JsonResponse({"error": "Ward type is required"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM find_bed_for_patient(%s, %s)", [ward_type, bed_type]
            )
            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, cursor.fetchone()))

            # Extract the 'beds' field which contains the actual bed data array
            beds_data = result.get("beds", [])

            # If it's a string (JSONB sometimes gets converted to string), parse it
            if isinstance(beds_data, str):
                import json

                beds_data = json.loads(beds_data)

            # Return the array of beds directly
            return JsonResponse(beds_data, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def reserve_bed(request):
    """Reserve a bed for a patient."""
    if request.method == "POST":
        data = json.loads(request.body)
        bed_id = data.get("bed_id")
        patient_name = data.get("patient_name")
        patient_username = request.session.get("patient_username")

        if not bed_id or not patient_username:
            return JsonResponse(
                {"error": "Bed ID and patient username are required"}, status=400
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT public.admit_patient(%s, %s, %s)",
                    [bed_id, patient_username, patient_name],
                )
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def patient_admission_record_page(request):
    return render(request, "patient_admission_history.html")


def current_admission(request):
    """API endpoint to get current admission for a patient."""
    patient_username = request.session.get("login_form_data", {}).get(
        "username"
    ) or request.session.get("patient_username")

    if not patient_username:
        return JsonResponse(
            {"error": "Not authenticated", "has_active_admission": False}, status=401
        )

    print(f"Debug: patient_username={patient_username}")

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM public.get_current_admission(%s)", [patient_username]
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            # Handle the case where no data is returned
            if row is None:
                return JsonResponse({"has_active_admission": False})

            result = dict(zip(columns, row))

            # Get actual names for doctor and nurse
            if result.get("doctor_username"):
                cursor.execute(
                    "SELECT public.get_name(%s)", [result["doctor_username"]]
                )
                doctor_name = cursor.fetchone()[0]
                result["doctor_name"] = doctor_name

            if result.get("nurse_username"):
                cursor.execute("SELECT public.get_name(%s)", [result["nurse_username"]])
                nurse_name = cursor.fetchone()[0]
                result["nurse_name"] = nurse_name

            # Convert datetime objects to string representation
            if result.get("check_in_date"):
                result["check_in_date"] = result["check_in_date"].isoformat()
            if result.get("check_out_date"):
                result["check_out_date"] = result["check_out_date"].isoformat()

            return JsonResponse(result)
    except Exception as e:
        print(f"Error in current_admission: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse(
            {"error": str(e), "has_active_admission": False}, status=500
        )


def get_admissions(request):
    """API endpoint to get all admissions for a patient."""
    patient_username = request.session.get("login_form_data", {}).get(
        "username"
    ) or request.session.get("patient_username")

    if not patient_username:
        return JsonResponse({"error": "Not authenticated"}, status=401)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM public.get_patient_admissions(%s)", [patient_username]
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            result = []
            for row in rows:
                admission = dict(zip(columns, row))

                # Convert datetime objects to string representation
                if admission.get("check_in_date"):
                    admission["check_in_date"] = admission["check_in_date"].isoformat()
                if admission.get("check_out_date"):
                    admission["check_out_date"] = admission[
                        "check_out_date"
                    ].isoformat()

                result.append(admission)

            return JsonResponse(result, safe=False)
    except Exception as e:
        print(f"Error in get_admissions: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


def add_patient_notes(request):
    """API endpoint to add a note for a patient."""
    if request.method == "POST":
        data = json.loads(request.body)
        patient_username = request.session.get("patient_username")
        note = data.get("note")

        if not patient_username or not note:
            return JsonResponse(
                {"error": "Patient username and note are required"}, status=400
            )

        try:
            # First, get the current admission ID for the patient
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM public.get_current_admission(%s)", [patient_username]
                )
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()

                if not row:
                    return JsonResponse(
                        {"error": "No active admission found"}, status=400
                    )

                result = dict(zip(columns, row))
                admission_id = result.get("admission_id")

                if not admission_id:
                    return JsonResponse({"error": "No admission ID found"}, status=400)

                # Now call the correct function with admission_id and note
                cursor.execute(
                    "SELECT public.add_patient_bed_note(%s, %s)", [admission_id, note]
                )

            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error adding patient note: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def get_doctor_notes(request, admission_id):
    """API endpoint to get doctor notes for a specific admission."""
    try:
        with connection.cursor() as cursor:
            # Call the SQL function to get doctor notes
            cursor.execute(
                "SELECT * FROM public.get_doctor_notes(%s)",
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

                # Add author_type for frontend consistency
                note["author_type"] = "doctor"

        return JsonResponse({"success": True, "notes": notes})
    except Exception as e:
        import traceback

        print(f"Error in get_doctor_notes: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def make_discharge_request(request):
    """API endpoint to make a discharge request."""
    if request.method == "POST":
        data = json.loads(request.body)
        admission_id = data.get("admission_id")

        if not admission_id:
            return JsonResponse({"error": "Admission ID is required"}, status=400)

        try:
            with connection.cursor() as cursor:
                # Call the SQL function to make a discharge request
                cursor.execute(
                    "SELECT public.create_discharge_request(%s)", [admission_id]
                )

            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error making discharge request: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def patient_past_appointment_page(request):
    """Render the past appointment page."""
    return render(request, "patient_past_appointments_page.html")


def fetch_past_appointments(request):
    """API endpoint to get past appointments for a patient."""
    username = request.session.get("patient_username") or request.session.get(
        "login_form_data", {}
    ).get("username")
    user_type = "patient"

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

            doctor_username = item["related_user"]
            cursor.execute("SELECT public.get_name(%s)", [doctor_username])
            doctor_name = cursor.fetchone()[0]
            item["doctor_name"] = doctor_name

    response_data = json.dumps(data)
    return HttpResponse(response_data, content_type="application/json")


# Add this function at the end of the file


def get_prescription(request, appointment_id):
    """API endpoint to get a prescription for a specific appointment."""
    try:
        with connection.cursor() as cursor:
            # Get the appointment details first to verify it belongs to this patient
            patient_username = request.session.get(
                "patient_username"
            ) or request.session.get("login_form_data", {}).get("username")

            # Check if the appointment belongs to this patient
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM appointments 
                WHERE appointment_id = %s AND patient_username = %s
                """,
                [appointment_id, patient_username],
            )
            count = cursor.fetchone()[0]
            if count == 0:
                return JsonResponse({"error": "Appointment not found"}, status=404)

            # Fetch the prescription
            cursor.execute(
                """
                SELECT p.*, d.degrees as doctor_degrees
                FROM prescriptions p
                JOIN doctors d ON p.prescribed_by = d.username
                WHERE p.appointment_id = %s
                """,
                [appointment_id],
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            if not row:
                return JsonResponse({"error": "No prescription found"}, status=404)

            prescription = dict(zip(columns, row))

            # Format dates and arrays
            if "created_at" in prescription and prescription["created_at"]:
                prescription["created_at"] = prescription["created_at"].strftime(
                    "%Y-%m-%d"
                )

            if "doctor_degrees" in prescription and prescription["doctor_degrees"]:
                if isinstance(prescription["doctor_degrees"], list):
                    prescription["doctor_degrees"] = ", ".join(
                        prescription["doctor_degrees"]
                    )
                else:
                    prescription["doctor_degrees"] = (
                        prescription["doctor_degrees"].strip("{}").replace(",", ", ")
                    )

            return JsonResponse(prescription)
    except Exception as e:
        print(f"Error fetching prescription: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
