from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class FeedbackEngine:
    """
    Generates structured feedback via OpenAI or a deterministic fallback.
    """

    def __init__(self, rubric_prompt: str = ""):
        self.rubric_prompt = rubric_prompt
        self._client = None

    def _load_client(self):
        if self._client is not None or not settings.OPENAI_API_KEY:
            return
        try:
            from openai import OpenAI

            self._client = OpenAI()
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenAI client unavailable: %s", exc)
            self._client = None

    def generate(self, question: str, answer: str, score: float) -> str:
        self._load_client()
        if self._client is None:
            return (
                f"Score: {score:.1f}/100\n"
                f"Strengths: Clear articulation of key ideas.\n"
                f"Next steps: Revisit the rubric focus areas. {self.rubric_prompt[:140]}"
            )

        prompt = (
            "You are an accessible learning assistant. "
            "Produce concise, empathetic feedback for visually impaired learners. "
            f"Rubric:\n{self.rubric_prompt}\nQuestion: {question}\nAnswer: {answer}\n"
            f"Score: {score:.1f}.\nReply with bullet points."
        )
        try:
            response = self._client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
            )
            return response.output_text
        except Exception as exc:  # pragma: no cover
            logger.warning("LLM feedback failed, fallback text used: %s", exc)
            return (
                f"Score: {score:.1f}/100.\n"
                "Feedback unavailable; please review rubric with your teacher."
            )

