from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from assessments.models import Assessment, Question


class StudentDashboardViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student",
            password="pass",
            role=User.Roles.STUDENT,
        )
        teacher = User.objects.create_user(
            username="teacher",
            password="pass",
            role=User.Roles.TEACHER,
        )
        self.assessment = Assessment.objects.create(
            teacher=teacher,
            title="Algebra Basics",
            subject="Math",
        )
        Question.objects.create(
            assessment=self.assessment,
            text="Define a variable.",
            expected_answer="A symbol representing a number.",
            order=1,
        )

    def test_student_can_see_dashboard(self):
        client = Client()
        client.login(username="student", password="pass")
        response = client.get(reverse("student-dashboard"))
        self.assertContains(response, "Algebra Basics")

    def test_attempt_created_when_starting_assessment(self):
        client = Client()
        client.login(username="student", password="pass")
        response = client.get(reverse("student-assessment", args=[self.assessment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.student.attempts.count(), 1)

