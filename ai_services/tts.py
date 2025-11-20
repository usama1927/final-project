from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    """
    Converts feedback text to an mp3 file using gTTS when available.
    """

    def __init__(self, voice: Optional[str] = None):
        self.voice = voice or "en"

    def synthesize(self, text: str, filename: str) -> Optional[str]:
        if not text:
            return None
        media_root = Path(settings.MEDIA_ROOT) / "responses" / "tts"
        media_root.mkdir(parents=True, exist_ok=True)
        output_path = media_root / f"{filename}.mp3"
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=self.voice[:2])
            tts.save(output_path)
            return str(output_path.relative_to(settings.MEDIA_ROOT))
        except Exception as exc:  # pragma: no cover
            logger.warning("TTS failed: %s", exc)
            return None

