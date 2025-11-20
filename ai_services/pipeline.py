from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .asr import ASREngine
from .feedback import FeedbackEngine
from .scoring import ScoringEngine
from .tts import TextToSpeechEngine
from .utils import ScoreResult, compute_wer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    transcription: str
    transcription_confidence: float
    wer: float
    score: float
    rationale: str
    feedback_text: str
    feedback_audio: Optional[str]
    latency_ms: int
    metadata: dict


class AssessmentPipeline:
    def __init__(self):
        self.asr = ASREngine()
        self.scoring = ScoringEngine()
        self.feedback = FeedbackEngine()
        self.tts = TextToSpeechEngine()

    def process_audio(
        self,
        audio_path: Path,
        expected_answer: str,
        rubric: str,
        question_text: str,
    ) -> PipelineResult:
        asr_result = self.asr.transcribe(audio_path)
        transcription = asr_result["text"]
        confidence = asr_result["confidence"]
        return self._finalize(
            transcription=transcription,
            confidence=confidence,
            expected_answer=expected_answer,
            rubric=rubric,
            question_text=question_text,
        )

    def process_text(
        self,
        transcription: str,
        expected_answer: str,
        rubric: str,
        question_text: str,
    ) -> PipelineResult:
        return self._finalize(
            transcription=transcription,
            confidence=1.0,
            expected_answer=expected_answer,
            rubric=rubric,
            question_text=question_text,
        )

    def _finalize(
        self,
        transcription: str,
        confidence: float,
        expected_answer: str,
        rubric: str,
        question_text: str,
    ) -> PipelineResult:
        start = time.monotonic()
        score_result: ScoreResult = self.scoring.score(expected_answer, transcription, rubric)
        wer_value = compute_wer(expected_answer, transcription)

        feedback_text = self.feedback.generate(question_text, transcription, score_result.score)
        audio_key = self.tts.synthesize(feedback_text, filename=f"feedback-{int(time.time())}")

        latency = int((time.monotonic() - start) * 1000)

        metadata = {
            "asr_model": self.asr.model_name,
            "nlp_model": self.scoring.model_name,
            "confidence": confidence,
            "coverage": score_result.coverage_breakdown,
        }

        return PipelineResult(
            transcription=transcription,
            transcription_confidence=confidence,
            wer=wer_value,
            score=score_result.score,
            rationale=score_result.rationale,
            feedback_text=feedback_text,
            feedback_audio=audio_key,
            latency_ms=latency,
            metadata=metadata,
        )

