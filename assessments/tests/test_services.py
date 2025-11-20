from unittest import mock

from django.test import TestCase

from accounts.models import User
from assessments.models import Assessment, Question, Attempt, Response
from assessments import services


class EvaluateTranscriptionTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("teach", password="pass", role=User.Roles.TEACHER)
        self.student = User.objects.create_user("stud", password="pass", role=User.Roles.STUDENT)
        self.assessment = Assessment.objects.create(teacher=self.teacher, title="Science", subject="Bio")
        self.question = Question.objects.create(
            assessment=self.assessment,
            text="What is photosynthesis?",
            expected_answer="Plants convert light to energy.",
            order=1,
        )
        self.attempt = Attempt.objects.create(assessment=self.assessment, student=self.student)
        self.response = Response.objects.create(attempt=self.attempt, question=self.question)

    @mock.patch.object(services.pipeline, "process_text")
    def test_evaluate_transcription_updates_response(self, mock_process):
        mock_process.return_value = mock.Mock(
            transcription="Plants convert light to energy.",
            transcription_confidence=0.9,
            wer=0.0,
            score=95.0,
            rationale="Great answer",
            feedback_text="Excellent clarity.",
            feedback_audio=None,
            latency_ms=1200,
            metadata={"asr_model": "mock"},
        )
        services.evaluate_transcription(self.response, "Plants convert light to energy.")
        self.response.refresh_from_db()
        self.assertEqual(self.response.score, 95.0)
        self.assertEqual(self.attempt.responses.count(), 1)

