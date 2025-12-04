import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView

from .forms import AssessmentForm, QuestionFormSet, ResponseForm
from .models import Assessment, Attempt, Response
from .services import evaluate_transcription

logger = logging.getLogger(__name__)


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_student()


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_teacher()


class StudentDashboardView(StudentRequiredMixin, ListView):
    template_name = "student/dashboard.html"
    context_object_name = "assessments"

    def get_queryset(self):
        return Assessment.objects.filter(is_active=True).order_by("subject")


class StudentAssessmentView(StudentRequiredMixin, TemplateView):
    template_name = "student/assessment_session.html"

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(Assessment, pk=kwargs["pk"], is_active=True)
        self.attempt = self._get_or_create_attempt(request.user)
        return super().dispatch(request, *args, **kwargs)

    def _get_or_create_attempt(self, user):
        attempt, created = Attempt.objects.get_or_create(
            assessment=self.assessment,
            student=user,
            status=Attempt.Status.IN_PROGRESS,
            defaults={"model_version": settings.ASR_MODEL_NAME},
        )
        
        # Always ensure responses exist for all current questions
        # This handles cases where questions were added after attempt creation
        questions = self.assessment.questions.all()
        if not questions.exists():
            logger.warning(
                f"Assessment '{self.assessment.title}' (ID: {self.assessment.id}) "
                f"has no questions. Teacher: {self.assessment.teacher.username}"
            )
        else:
            # Use get_or_create to ensure all questions have responses
            # This is safe even if responses already exist
            for question in questions:
                Response.objects.get_or_create(
                    attempt=attempt,
                    question=question
                )
            logger.info(
                f"Ensured {questions.count()} response(s) exist for attempt {attempt.id}"
            )
        
        return attempt

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        responses = (
            self.attempt.responses.select_related("question")
            .order_by("question__order")
        )
        response_forms = [
            (response, ResponseForm(instance=response)) for response in responses
        ]
        
        # Check if assessment has questions
        question_count = self.assessment.questions.count()
        response_count = responses.count()
        
        # Debug logging
        logger.info(
            f"Assessment '{self.assessment.title}' (ID: {self.assessment.id}): "
            f"{question_count} question(s) in assessment, "
            f"{response_count} response(s) in attempt {self.attempt.id}"
        )
        
        if question_count == 0:
            messages.warning(
                self.request,
                f"This assessment '{self.assessment.title}' has no questions. "
                "Please contact your teacher to add questions."
            )
        elif response_count == 0 and question_count > 0:
            # This shouldn't happen with our fix, but log it if it does
            logger.error(
                f"Attempt {self.attempt.id} has no responses but assessment has "
                f"{question_count} questions. This indicates a bug."
            )
            messages.error(
                self.request,
                "An error occurred loading questions. Please refresh the page."
            )
        
        context.update(
            {
                "assessment": self.assessment,
                "attempt": self.attempt,
                "response_forms": response_forms,
                "question_count": question_count,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        response = get_object_or_404(
            Response,
            attempt=self.attempt,
            question_id=request.POST.get("question_id"),
        )
        form = ResponseForm(request.POST, instance=response)
        if form.is_valid():
            evaluate_transcription(response, form.cleaned_data["transcription"])
            messages.success(request, "Response scored successfully.")
        else:
            messages.error(request, "Please fix the errors before submitting.")
        return redirect(request.path)


class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "teacher/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessments = Assessment.objects.filter(teacher=self.request.user).prefetch_related("questions")
        attempts = (
            Attempt.objects.filter(assessment__teacher=self.request.user)
            .select_related("student", "assessment")
            .order_by("-started_at")[:10]
        )
        context.update({"assessments": assessments, "attempts": attempts})
        return context


class AssessmentCreateView(TeacherRequiredMixin, View):
    template_name = "teacher/assessment_form.html"
    success_url = reverse_lazy("teacher-dashboard")

    def get(self, request, *args, **kwargs):
        return self._render()

    def post(self, request, *args, **kwargs):
        form = AssessmentForm(request.POST)
        draft_assessment = Assessment(teacher=request.user)
        formset = QuestionFormSet(request.POST, request.FILES, instance=draft_assessment)
        if form.is_valid() and formset.is_valid():
            assessment = form.save(commit=False)
            assessment.teacher = request.user
            assessment.save()
            formset.instance = assessment
            formset.save()
            messages.success(request, "Assessment created.")
            return redirect(self.success_url)
        messages.error(request, "Please review the errors below.")
        return self._render(form, formset)

    def _render(self, form=None, formset=None):
        form = form or AssessmentForm()
        draft_assessment = getattr(self, "_draft_assessment", None) or Assessment(
            teacher=self.request.user
        )
        formset = formset or QuestionFormSet(instance=draft_assessment)
        return render(
            self.request,
            self.template_name,
            {"form": form, "formset": formset},
        )


class AssessmentResultsView(TeacherRequiredMixin, TemplateView):
    template_name = "teacher/assessment_results.html"

    def dispatch(self, request, *args, **kwargs):
        self.assessment = get_object_or_404(
            Assessment, pk=kwargs["pk"], teacher=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = (
            self.assessment.attempts.select_related("student")
            .prefetch_related("responses__question")
            .order_by("-started_at")
        )
        context.update({"assessment": self.assessment, "attempts": attempts})
        return context
