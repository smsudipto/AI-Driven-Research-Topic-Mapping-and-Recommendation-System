from django.db import models
from django.contrib.auth.models import AbstractUser

class Accounts(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='student')

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_supervisor(self):
        return self.role == 'supervisor'

    @property
    def is_admin_role(self):
        return self.role == 'admin'

    def __str__(self):
        return f"{self.username} ({self.role})"