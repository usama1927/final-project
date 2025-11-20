from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


def compute_wer(reference: str, hypothesis: str) -> float:
    """
    Simple word error rate implementation.
    """
    ref_tokens = reference.strip().split()
    hyp_tokens = hypothesis.strip().split()
    if not ref_tokens:
        return 0.0 if not hyp_tokens else 100.0

    d = [[0] * (len(hyp_tokens) + 1) for _ in range(len(ref_tokens) + 1)]

    for i in range(len(ref_tokens) + 1):
        d[i][0] = i
    for j in range(len(hyp_tokens) + 1):
        d[0][j] = j

    for i in range(1, len(ref_tokens) + 1):
        for j in range(1, len(hyp_tokens) + 1):
            substitution_cost = 0 if ref_tokens[i - 1] == hyp_tokens[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1,  # deletion
                d[i][j - 1] + 1,  # insertion
                d[i - 1][j - 1] + substitution_cost,  # substitution
            )

    wer = d[len(ref_tokens)][len(hyp_tokens)] / len(ref_tokens)
    return round(wer * 100, 2)


def harmonic_mean(values: Sequence[float]) -> float:
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return 0.0
    return round(len(non_zero) / sum(1 / v for v in non_zero), 2)


@dataclass
class ScoreResult:
    score: float
    rationale: str
    coverage_breakdown: dict[str, float]

