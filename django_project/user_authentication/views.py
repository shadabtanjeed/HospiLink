# django_project/user_authentication/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import connection
from django.db.utils import DatabaseError
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json


def index(request):
    return render(request, "login_page.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username").lower()  # Convert to lowercase
        password = request.POST.get("password")

        # Debug: Print retrieved username and password
        print(f"Username: {username}, Password: {password}")

        # Hash the password
        hash_object = hashlib.sha512(password.encode("utf-8"))
        password_hash = hash_object.hexdigest()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT public.login_user(%s, %s)
                    """,
                    [username, password_hash],
                )
                login_success = cursor.fetchone()[0]

            if login_success:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT public.find_user_type(%s)
                        """,
                        [username],
                    )
                    user_type = cursor.fetchone()[0]

                # Store login data in session
                login_form_data = {
                    "username": username,
                    "user_type": user_type,
                }

                request.session["login_form_data"] = login_form_data
                return redirect("login_success")

            else:
                return HttpResponse(
                    "Login failed: Invalid username or password", status=401
                )

        except DatabaseError as e:
            error_message = str(e)
            return HttpResponse(f"Login failed: {error_message}", status=400)

    return render(request, "login_page.html")


def forgot_password_view(request):
    return render(request, "forgot_password.html")


def signup_view(request):
    if request.method == "POST":
        try:
            # Common fields
            user_type = request.POST.get("user_type")
            username = request.POST.get("username")
            password = request.POST.get("password")
            security_question = request.POST.get("security_question")
            security_answer = request.POST.get("security_answer")
            phone_number = request.POST.get("phone_number")
            name = request.POST.get("name")
            gender = request.POST.get("gender")

            # Hash password and security answer
            hash_object = hashlib.sha512(password.encode("utf-8"))
            password_hash = hash_object.hexdigest()

            hash_object = hashlib.sha512(security_answer.encode("utf-8"))
            security_answer_hash = hash_object.hexdigest()

            with connection.cursor() as cursor:
                if user_type == "patient":
                    blood_group = request.POST.get("blood_group")
                    complexities = request.POST.get("complexities")
                    date_of_birth = request.POST.get("dob")

                    cursor.execute(
                        """
                        SELECT public.signup_users(%s, %s, %s, %s::users_type, %s, %s, %s, %s::bloodgroup, %s, NULL, NULL, NULL, NULL, %s::date, %s, NULL, NULL, NULL)
                        """,
                        [
                            username,
                            name,
                            password_hash,
                            user_type,
                            security_question,
                            security_answer_hash,
                            phone_number,
                            blood_group,
                            complexities,
                            date_of_birth,
                            gender,
                        ],
                    )
                else:  # doctor
                    specialization = request.POST.get("specialization")
                    visiting_days = request.POST.getlist("available_days")
                    from_time = request.POST.get("from_time")
                    to_time = request.POST.get("to_time")
                    degrees = request.POST.getlist("doctor_degrees")
                    doctor_fee = request.POST.get("doctor_fee")
                    avg_time = request.POST.get("avg_time")

                    # convert into number
                    doctor_fee = int(doctor_fee)
                    avg_time = int(avg_time)

                    # Map short day names to enum values
                    day_mapping = {
                        "mon": "monday",
                        "tue": "tuesday",
                        "wed": "wednesday",
                        "thu": "thursday",
                        "fri": "friday",
                        "sat": "saturday",
                        "sun": "sunday",
                    }

                    # Convert days
                    enum_days = [day_mapping[day.lower()] for day in visiting_days]
                    visiting_days_array = "{" + ",".join(enum_days) + "}"

                    # Convert degrees list to PostgreSQL array format
                    degrees_array = "{" + ",".join(degrees) + "}"

                    cursor.execute(
                        """
                        SELECT public.signup_users(%s, %s, %s, %s::users_type, %s, %s, %s, NULL, NULL, %s, %s::day_of_week[], %s::time, %s::time, NULL, %s, %s::text[], %s, %s)
                        """,
                        [
                            username,
                            name,
                            password_hash,
                            user_type,
                            security_question,
                            security_answer_hash,
                            phone_number,
                            specialization,
                            visiting_days_array,
                            from_time,
                            to_time,
                            gender,
                            degrees_array,
                            doctor_fee,
                            avg_time,
                        ],
                    )

                    # Handle image upload
                    image = request.FILES.get("image")
                    image_data = image.read() if image else None

                    cursor.execute(
                        """
                        SELECT public.add_doctor_profile_pic(%s, %s)
                        """,
                        [
                            username,
                            image_data,
                        ],
                    )

            # Store form data in session
            form_data = {
                "username": username,
                "user_type": user_type,
                "phone_number": phone_number,
                "name": name,
            }

            # Add type-specific data
            if user_type == "patient":
                form_data.update(
                    {
                        "blood_group": request.POST.get("blood_group"),
                        "complexities": request.POST.get("complexities"),
                        "date of birth": request.POST.get("dob"),
                        "gender": request.POST.get("gender"),
                    }
                )
            else:
                form_data.update(
                    {
                        "specialization": request.POST.get("specialization"),
                        "available_days": request.POST.getlist("available_days"),
                        "from_time": request.POST.get("from_time"),
                        "to_time": request.POST.get("to_time"),
                        "gender": request.POST.get("gender"),
                        "degrees": request.POST.getlist("doctor_degrees"),
                    }
                )

            request.session["form_data"] = form_data
            return JsonResponse({"success": True, "message": "Signup successful"})

        except DatabaseError as e:
            error_message = str(e)
            return JsonResponse(
                {"success": False, "message": f"Signup failed: {error_message}"},
                status=400,
            )

    return render(request, "signup_page.html")


def signup_success(request):
    # Retrieve the form data from the session
    form_data = request.session.get("form_data", {})
    print(form_data)
    return HttpResponse(f"Signup successful! Data: {form_data}")


def login_success(request):
    # Retrieve the form data from the session
    form_data = request.session.get("login_form_data", {})
    username = form_data.get("username", "")

    # Check the user type using the find_user_type function
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.find_user_type(%s)", [username])
        user_type = cursor.fetchone()[0]

    if user_type == "patient":
        request.session["patient_username"] = username
        return redirect(f"/patient/?username={username}")
    else:
        return HttpResponse("Login successful, but you are not a patient.")


def check_username(request):
    username = request.GET.get("username", "")
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.check_user_exists(%s)", [username])
        exists = cursor.fetchone()[0]
    return JsonResponse({"exists": exists})


def get_security_question(request):
    username = request.GET.get("username", "")
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.show_security_question(%s)", [username])
        question = cursor.fetchone()[0]
    return JsonResponse({"question": question})


@csrf_exempt
def verify_security_question(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username", "")
        answer = data.get("security_answer", "")

        # Hash the answer
        hash_object = hashlib.sha512(answer.encode("utf-8"))
        answer_hash = hash_object.hexdigest()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT public.verify_security_question(%s, %s)",
                [username, answer_hash],
            )
            correct = cursor.fetchone()[0]
        return JsonResponse({"correct": correct})
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def update_password(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username", "")
        answer = data.get("security_answer", "")
        new_password = data.get("password", "")

        # Hash the answer
        hash_object = hashlib.sha512(answer.encode("utf-8"))
        answer_hash = hash_object.hexdigest()

        # Hash the new password
        hash_object = hashlib.sha512(new_password.encode("utf-8"))
        new_password_hash = hash_object.hexdigest()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT public.reset_user_password(%s, %s, %s)",
                [username, answer_hash, new_password_hash],
            )
            correct = cursor.fetchone()[0]
        return JsonResponse({"correct": correct})
    return JsonResponse({"error": "Invalid request method"}, status=400)
