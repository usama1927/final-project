from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Accessibility Preferences",
            {"fields": ("role", "audio_feedback_enabled", "preferred_voice", "timezone")},
        ),
    )
    list_display = ("username", "email", "role", "audio_feedback_enabled")
    list_filter = ("role", "audio_feedback_enabled", "is_active")
