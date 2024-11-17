# django_project/patient/views.py
from django.shortcuts import render
from django.db import connection


def index(request):
    # Your existing index view code
    return render(request, "patient_page.html")


def search_doctor(request):
    # Your logic to handle the search doctor page
    return render(request, "search_doctor.html")
