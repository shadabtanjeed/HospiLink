from django.shortcuts import render
from django.db import connection


def index(request):
    username = request.session.get("receptionist_username", "")

    with connection.cursor() as cursor:
        cursor.execute("SELECT public.get_name(%s)", [username])
        name = cursor.fetchone()[0]

    return render(
        request, "receptionist_page.html", {"username": username, "name": name}
    )
