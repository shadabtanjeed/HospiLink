# django_project/user_authentication/models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255)
    password_hash = models.TextField()
    user_type = models.CharField(max_length=255)
    security_question = models.TextField()
    security_answer_hash = models.TextField()

    def __str__(self):
        return self.username