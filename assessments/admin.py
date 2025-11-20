from django.contrib import admin

from .models import Assessment, Attempt, ProcessingLog, Question, Response


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "teacher", "is_active", "created_at")
    list_filter = ("subject", "is_active", "created_at")
    search_fields = ("title", "subject", "teacher__username")
    inlines = [QuestionInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("assessment", "student", "status", "overall_score", "overall_wer")
    list_filter = ("status", "assessment__subject")
    search_fields = ("assessment__title", "student__username")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "score", "wer", "created_at")
    list_filter = ("question__assessment",)
    search_fields = ("transcription", "feedback_text")


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ("response", "event", "latency_ms", "created_at")
    list_filter = ("event",)
