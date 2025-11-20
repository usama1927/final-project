from django import forms
from django.forms import inlineformset_factory

from .models import Assessment, Question, Response


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = [
            "title",
            "subject",
            "instructions",
            "rubric_prompt",
            "language",
            "is_active",
        ]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "expected_answer", "rubric", "order", "audio_prompt"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 2}),
            "expected_answer": forms.Textarea(attrs={"rows": 2}),
            "rubric": forms.Textarea(attrs={"rows": 2}),
        }


QuestionFormSet = inlineformset_factory(
    Assessment,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True,
)


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ["transcription"]
        widgets = {
            "transcription": forms.Textarea(
                attrs={
                    "rows": 3,
                    "aria-label": "Answer transcription",
                    "placeholder": "Speak your answer or type it here.",
                }
            )
        }

