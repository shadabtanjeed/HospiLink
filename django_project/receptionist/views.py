from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
import json



def index(request):
    username = request.session.get("receptionist_username", "")

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_name(%s)", [username])
        name = cursor.fetchone()[0]

    return render(
        request, "receptionist_page.html", {"username": username, "name": name}
    )


def add_blood_donor(request):
    return render(request, "add_blood_donor.html")

from patient.views import fetch_doctors  # reuse fn

def store_blood_donor_details(request):
    if request.method == "POST":
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)

            name = data.get("name")
            blood_group = data.get("blood_group")
            complexities = data.get("complexities")
            last_donation_date = data.get("last_donation_date")
            mobile_numbers = data.get("mobile_numbers", [])
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            # Check for duplicate phone numbers
            for mobile_number in mobile_numbers:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT public.find_duplicate_phone_number(%s)", [mobile_number]
                    )
                    result = cursor.fetchone()[0]
                    if result:
                        return JsonResponse(
                            {
                                "success": False,
                                "message": f"Mobile number {mobile_number} already exists",
                            },
                            status=400,
                        )

            # Store blood donor details in the database
            with connection.cursor() as cursor:
                # Create point from latitude and longitude (swap latitude and longitude)
                point = f"({longitude},{latitude})"

                # Convert mobile numbers list to SQL array
                phone_numbers_array = "{" + ",".join(mobile_numbers) + "}"

                # Call the add_blood_donor function
                cursor.execute(
                    """
                    SELECT public.add_blood_donor(
                        %s, %s, %s, %s::timestamp, %s::point, %s::bpchar[]
                    )
                    """,
                    [
                        name,
                        blood_group,
                        complexities,
                        last_donation_date,
                        point,
                        phone_numbers_array,
                    ],
                )

            return JsonResponse(
                {"success": True, "message": "Blood donor added successfully"}
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid JSON data"}, status=400
            )
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse(
                {"success": False, "message": "Failed to add blood donor"}, status=500
            )

    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

def blood_repo_receptionist(request):
    return render(request, 'blood_repo_receptionist.html')

def check_patient_exists(request):
    phone_number = request.GET.get('phone_number', '')

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.check_patient_exists(%s)", [phone_number])
        exists = cursor.fetchone()[0]

    return JsonResponse({'exists': exists})

def create_patient_account(request):
    return render(request, 'recptions_signing_up_patient.html')

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

def receptionist_search_doctor(request):
    patient_phone_number = request.GET.get("patient_phone_number", "")

    # Fetch patient username using the phone number
    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM patients WHERE phone_no = '%s'", [patient_phone_number])
        patient_username = cursor.fetchone()

    # If no patient is found, set patient_username to an empty string
    patient_username = patient_username[0] if patient_username else ""

    # Fetch the list of doctors
    doctors = fetch_doctors()

    context = {
        "patient_username": patient_username,
        "doctors": doctors,
    }
    return render(request, "receptionist_search_doctor.html", context)