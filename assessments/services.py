from __future__ import annotations

import logging
from pathlib import Path

from django.db import transaction

from ai_services.pipeline import AssessmentPipeline

from .models import Attempt, ProcessingLog, Response

logger = logging.getLogger(__name__)


pipeline = AssessmentPipeline()


@transaction.atomic
def evaluate_response(response: Response) -> Response:
    if not response.raw_audio:
        logger.info("No audio uploaded for response %s", response.pk)
        return response

    audio_path = Path(response.raw_audio.path)
    question = response.question

    result = pipeline.process_audio(
        audio_path=audio_path,
        expected_answer=question.expected_answer,
        rubric=question.rubric,
        question_text=question.text,
    )

    response.transcription = result.transcription
    response.transcription_confidence = result.transcription_confidence
    response.score = result.score
    response.feedback_text = result.feedback_text
    if result.feedback_audio:
        response.feedback_audio.name = result.feedback_audio
    response.wer = result.wer
    response.ai_metadata = result.metadata
    response.save()

    ProcessingLog.objects.create(
        response=response,
        event="pipeline_completed",
        detail=result.metadata | {"rationale": result.rationale},
        latency_ms=result.latency_ms,
    )

    _update_attempt_metrics(response.attempt)

    return response


@transaction.atomic
def evaluate_transcription(response: Response, transcription: str) -> Response:
    question = response.question
    result = pipeline.process_text(
        transcription=transcription,
        expected_answer=question.expected_answer,
        rubric=question.rubric,
        question_text=question.text,
    )

    response.transcription = result.transcription
    response.score = result.score
    response.feedback_text = result.feedback_text
    if result.feedback_audio:
        response.feedback_audio.name = result.feedback_audio
    response.wer = result.wer
    response.ai_metadata = result.metadata
    response.save()

    ProcessingLog.objects.create(
        response=response,
        event="text_submission_scored",
        detail=result.metadata | {"rationale": result.rationale},
        latency_ms=result.latency_ms,
    )
    _update_attempt_metrics(response.attempt)
    return response


def _update_attempt_metrics(attempt: Attempt):
    responses = attempt.responses.exclude(score__isnull=True)
    if not responses.exists():
        return
    attempt.overall_score = sum(r.score for r in responses) / responses.count()
    attempt.overall_wer = sum(r.wer or 0 for r in responses) / responses.count()
    attempt.status = Attempt.Status.COMPLETED
    attempt.save(update_fields=["overall_score", "overall_wer", "status"])

