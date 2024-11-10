from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    return render(request, "login_page.html")


def login_view(request):
    return render(request, "login_page.html")


def signup_view(request):
    return render(request, "signup_page.html")
