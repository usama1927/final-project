from django.urls import path

from .views import (
    AssessmentCreateView,
    AssessmentResultsView,
    StudentAssessmentView,
    StudentDashboardView,
    TeacherDashboardView,
)

urlpatterns = [
    path("student/dashboard/", StudentDashboardView.as_view(), name="student-dashboard"),
    path(
        "student/assessment/<int:pk>/",
        StudentAssessmentView.as_view(),
        name="student-assessment",
    ),
    path("teacher/dashboard/", TeacherDashboardView.as_view(), name="teacher-dashboard"),
    path(
        "teacher/assessment/create/",
        AssessmentCreateView.as_view(),
        name="assessment-create",
    ),
    path(
        "teacher/assessment/<int:pk>/results/",
        AssessmentResultsView.as_view(),
        name="assessment-results",
    ),
]

