from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class UserModelTests(TestCase):
    def test_dashboard_url_for_roles(self):
        teacher = User.objects.create_user(
            username="teach",
            password="pass",
            role=User.Roles.TEACHER,
        )
        student = User.objects.create_user(
            username="stud",
            password="pass",
            role=User.Roles.STUDENT,
        )

        self.assertEqual(teacher.get_dashboard_url(), reverse("teacher-dashboard"))
        self.assertEqual(student.get_dashboard_url(), reverse("student-dashboard"))
from django.test import TestCase

# Create your tests here.
