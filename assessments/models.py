from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Assessment(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=120)
    instructions = models.TextField(blank=True)
    rubric_prompt = models.TextField(
        help_text="Structured prompt to guide LLM feedback generation.",
        blank=True,
    )
    language = models.CharField(max_length=32, default="en")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):
    assessment = models.ForeignKey(
        Assessment,
        related_name="questions",
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    expected_answer = models.TextField()
    rubric = models.TextField(
        help_text="JSON or markdown rubric with scoring guidance.",
        blank=True,
    )
    order = models.PositiveIntegerField(default=1)
    audio_prompt = models.FileField(upload_to="question_prompts/", blank=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}"


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    assessment = models.ForeignKey(
        Assessment,
        related_name="attempts",
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        User,
        related_name="attempts",
        on_delete=models.CASCADE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IN_PROGRESS
    )
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_wer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    model_version = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-started_at"]
        unique_together = ("assessment", "student", "started_at")

    def __str__(self):
        return f"{self.student} - {self.assessment} ({self.status})"


class Response(models.Model):
    attempt = models.ForeignKey(
        Attempt,
        related_name="responses",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        Question,
        related_name="responses",
        on_delete=models.CASCADE,
    )
    transcription = models.TextField(blank=True)
    raw_audio = models.FileField(upload_to="responses/audio/", blank=True)
    transcription_confidence = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    feedback_audio = models.FileField(upload_to="responses/tts/", blank=True)
    wer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ai_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("attempt", "question")
        ordering = ["created_at"]

    def __str__(self):
        return f"Response {self.id} - Attempt {self.attempt_id}"


class ProcessingLog(models.Model):
    response = models.ForeignKey(
        Response,
        related_name="logs",
        on_delete=models.CASCADE,
    )
    event = models.CharField(max_length=120)
    detail = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Log {self.event} ({self.created_at})"
