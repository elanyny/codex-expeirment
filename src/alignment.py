from __future__ import annotations

from typing import Tuple

from .models import Market

NEGATIONS = {"not", "no", "fail", "fails", "under", "below", "against", "without"}


def _contains_negation(text: str) -> bool:
    words = set(text.lower().split())
    return any(word in words for word in NEGATIONS)


def align_outcomes(market_a: Market, market_b: Market) -> Tuple[bool, str, str]:
    """
    Returns (aligned, relation, reason):
      - relation "same" means YES<->YES and NO<->NO
      - relation "inverted" means YES<->NO and NO<->YES
    """
    neg_a = _contains_negation(market_a.title)
    neg_b = _contains_negation(market_b.title)

    if neg_a == neg_b:
        return True, "same", "matching polarity"
    return True, "inverted", "negation mismatch inferred"
