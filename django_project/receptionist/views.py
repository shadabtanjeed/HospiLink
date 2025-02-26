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