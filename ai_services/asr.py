from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class ASREngine:
    """
    Thin wrapper around a Whisper / Wav2Vec2 pipeline.
    Falls back to a mock transcription when GPU resources are unavailable.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self.model_name = model_name or settings.ASR_MODEL_NAME
        self.device = device
        self._pipeline = None

    def _load_pipeline(self):
        if self._pipeline is not None:
            return
        try:
            from transformers import pipeline

            self._pipeline = pipeline(
                task="automatic-speech-recognition",
                model=self.model_name,
                device=self.device or "cpu",
            )
            logger.info("Loaded ASR model %s", self.model_name)
        except Exception as exc:  # pragma: no cover - hardware specific
            logger.warning("Falling back to mock ASR: %s", exc)
            self._pipeline = None

    def transcribe(self, audio_path: Path) -> dict:
        self._load_pipeline()
        if self._pipeline is None:
            text = "Transcription unavailable during development."
            confidence = 0.0
        else:
            try:
                result = self._pipeline(str(audio_path))
                text = result.get("text", "")
                confidence = result.get("score", 0.0)
            except Exception as exc:  # pragma: no cover - runtime safety
                logger.error("ASR pipeline failed, falling back to empty transcription: %s", exc)
                text = ""
                confidence = 0.0
        return {
            "text": text.strip(),
            "confidence": confidence,
            "model": self.model_name,
        }

