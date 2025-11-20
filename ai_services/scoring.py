from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Optional

from django.conf import settings

from .utils import ScoreResult

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Hybrid rubric scorer that prioritizes semantic similarity.
    Falls back to heuristic scoring when transformer models are not available.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.NLP_MODEL_NAME
        self._embedder = None

    def _load_embedder(self):
        if self._embedder is not None:
            return
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModel.from_pretrained(self.model_name)

            def embed(text: str):
                inputs = tokenizer(text, return_tensors="pt", truncation=True)
                outputs = model(**inputs)
                return outputs.last_hidden_state.mean(dim=1)

            self._embedder = embed
            logger.info("Loaded NLP scoring model %s", self.model_name)
        except Exception as exc:  # pragma: no cover
            logger.warning("Falling back to heuristic scorer: %s", exc)
            self._embedder = None

    def _semantic_similarity(self, a: str, b: str) -> float:
        self._load_embedder()
        if not a or not b:
            return 0.0
        if self._embedder is None:
            ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
            return round(ratio * 100, 2)

        import torch  # pragma: no cover

        with torch.no_grad():
            emb_a = self._embedder(a)
            emb_b = self._embedder(b)
            similarity = torch.nn.functional.cosine_similarity(emb_a, emb_b)
            return round(float(similarity.item()) * 100, 2)

    def score(
        self,
        expected_answer: str,
        transcription: str,
        rubric: str = "",
    ) -> ScoreResult:
        similarity = self._semantic_similarity(expected_answer, transcription)
        coverage = min(100.0, similarity + (len(transcription.split()) > 0) * 5)
        coherence = min(100.0, similarity + (len(transcription) / 5))
        score = round((similarity * 0.6) + (coverage * 0.3) + (coherence * 0.1), 2)
        rationale = (
            f"Semantic similarity {similarity:.1f}%, coverage {coverage:.1f}%, "
            f"coherence {coherence:.1f}%.\nRubric: {rubric[:180]}"
        )
        return ScoreResult(
            score=score,
            rationale=rationale,
            coverage_breakdown={
                "semantic_similarity": similarity,
                "coverage": coverage,
                "coherence": coherence,
            },
        )

