# django_project/user_authentication/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
import hashlib



def index(request):
    return render(request, "login_page.html")

def login_view(request):
    return render(request, "login_page.html")

def signup_view(request):
    if request.method == "POST":
        user_type = request.POST.get("user_type")
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        blood_group = request.POST.get("blood_group")
        complexities = request.POST.get("complexities")
        specialization = request.POST.get("specialization")
        available_days = request.POST.getlist("available_days")
        from_time = request.POST.get("from_time")
        to_time = request.POST.get("to_time")
        security_question = request.POST.get("security_question")
        security_answer = request.POST.get("security_answer")

        hash_object = hashlib.sha512(password.encode('utf-8'))  
        password = hash_object.hexdigest()

        hash_object = hashlib.sha512(security_answer.encode('utf-8'))
        security_answer = hash_object.hexdigest()

        # Store the data in variables (for demonstration purposes)
        form_data = {
            "user_type": user_type,
            "username": username,
            "password": password,
            "phone_number": phone_number,
            "blood_group": blood_group,
            "complexities": complexities,
            "specialization": specialization,
            "available_days": available_days,
            "from_time": from_time,
            "to_time": to_time,
            "security_question": security_question,
            "security_answer": security_answer,
        }

        # Store the form data in the session
        request.session['form_data'] = form_data

        # Redirect to a success page
        return redirect('signup_success')

    return render(request, "signup_page.html")

def signup_success(request):
    # Retrieve the form data from the session
    form_data = request.session.get('form_data', {})
    print(form_data)
    return HttpResponse(f"Signup successful! Data: {form_data}")
