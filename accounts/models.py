from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    class Roles(models.TextChoices):
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
    )
    audio_feedback_enabled = models.BooleanField(default=True)
    preferred_voice = models.CharField(max_length=64, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    def is_teacher(self) -> bool:
        return self.role == self.Roles.TEACHER

    def is_student(self) -> bool:
        return self.role == self.Roles.STUDENT

    def get_dashboard_url(self) -> str:
        if self.is_teacher():
            return reverse("teacher-dashboard")
        return reverse("student-dashboard")

    @property
    def dashboard_url(self) -> str:
        return self.get_dashboard_url()
