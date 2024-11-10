# django_project/user_authentication/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import connection
from django.db.utils import DatabaseError
import hashlib
from django.http import JsonResponse


def index(request):
    return render(request, "login_page.html")


def login_view(request):
    return render(request, "login_page.html")


def signup_view(request):
    if request.method == "POST":
        # Common fields
        user_type = request.POST.get("user_type")
        username = request.POST.get("username")
        password = request.POST.get("password")
        security_question = request.POST.get("security_question")
        security_answer = request.POST.get("security_answer")
        phone_number = request.POST.get("phone_number")

        # Hash password and security answer
        hash_object = hashlib.sha512(password.encode("utf-8"))
        password_hash = hash_object.hexdigest()

        hash_object = hashlib.sha512(security_answer.encode("utf-8"))
        security_answer_hash = hash_object.hexdigest()

        try:
            with connection.cursor() as cursor:
                if user_type == "patient":
                    blood_group = request.POST.get("blood_group")
                    complexities = request.POST.get("complexities")

                    cursor.execute(
                        """
                        SELECT public.signup_users(%s, %s, %s::users_type, %s, %s, %s, %s::bloodgroup, %s, NULL, NULL, NULL, NULL)
                        """,
                        [
                            username,
                            password_hash,
                            user_type,
                            security_question,
                            security_answer_hash,
                            phone_number,
                            blood_group,
                            complexities,
                        ],
                    )
                else:  # doctor
                    specialization = request.POST.get("specialization")
                    visiting_days = request.POST.getlist("available_days")
                    from_time = request.POST.get("from_time")
                    to_time = request.POST.get("to_time")

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

                    cursor.execute(
                        """
                        SELECT public.signup_users(%s, %s, %s::users_type, %s, %s, %s, NULL, NULL, %s, %s::day_of_week[], %s::time, %s::time)
                        """,
                        [
                            username,
                            password_hash,
                            user_type,
                            security_question,
                            security_answer_hash,
                            phone_number,
                            specialization,
                            visiting_days_array,
                            from_time,
                            to_time,
                        ],
                    )

            # Store form data in session
            form_data = {
                "username": username,
                "user_type": user_type,
                "phone_number": phone_number,
            }

            # Add type-specific data
            if user_type == "patient":
                form_data.update(
                    {
                        "blood_group": request.POST.get("blood_group"),
                        "complexities": request.POST.get("complexities"),
                    }
                )
            else:
                form_data.update(
                    {
                        "specialization": request.POST.get("specialization"),
                        "available_days": request.POST.getlist("available_days"),
                        "from_time": request.POST.get("from_time"),
                        "to_time": request.POST.get("to_time"),
                    }
                )

            request.session["form_data"] = form_data
            return redirect("signup_success")

        except DatabaseError as e:
            error_message = str(e)
            return HttpResponse(f"Signup failed: {error_message}", status=400)

    return render(request, "signup_page.html")


def signup_success(request):
    # Retrieve the form data from the session
    form_data = request.session.get("form_data", {})
    print(form_data)
    return HttpResponse(f"Signup successful! Data: {form_data}")


def check_username(request):
    username = request.GET.get("username", "")
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.check_user_exists(%s)", [username])
        exists = cursor.fetchone()[0]
    return JsonResponse({"exists": exists})
