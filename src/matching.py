from __future__ import annotations

import re
import string
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Set, Tuple

from .models import CandidateFeatures, Market, MatchCandidate

SYNONYMS = {
    "election": "vote",
    "elections": "vote",
    "cpi": "inflation",
    "percent": "%",
}
STOPWORDS = {"will", "the", "a", "an", "by", "on", "in", "of", "to"}


DATE_RE = re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?\b", re.I)
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
WORD_RE = re.compile(r"[a-zA-Z%]+")


def normalize_text(text: str) -> str:
    text = text.lower().translate(str.maketrans("", "", string.punctuation.replace("%", "")))
    tokens = []
    for token in text.split():
        token = SYNONYMS.get(token, token)
        if token not in STOPWORDS:
            tokens.append(token)
    return " ".join(tokens)


def extract_entities(market: Market) -> Set[str]:
    source = f"{market.title} {market.resolution_rules}"
    entities: Set[str] = set()
    entities.update(x.group(0).lower() for x in DATE_RE.finditer(source))
    entities.update(x.group(0).lower() for x in NUMBER_RE.finditer(source))
    tokens = [m.group(0).lower() for m in WORD_RE.finditer(source)]
    entities.update(t for t in tokens if len(t) > 2 and t not in STOPWORDS)
    return entities


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(a=normalize_text(a), b=normalize_text(b)).ratio()


def jaccard_overlap(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def date_score(date_a: datetime, date_b: datetime) -> float:
    days = abs((date_a.date() - date_b.date()).days)
    if days == 0:
        return 1.0
    if days <= 3:
        return 0.7
    if days <= 7:
        return 0.3
    return 0.0


def score_candidate(market_a: Market, market_b: Market) -> MatchCandidate:
    entities_a = extract_entities(market_a)
    entities_b = extract_entities(market_b)

    t_score = text_similarity(market_a.title, market_b.title)
    e_score = jaccard_overlap(entities_a, entities_b)
    d_score = date_score(market_a.end_time, market_b.end_time)
    r_score = text_similarity(market_a.resolution_rules, market_b.resolution_rules)

    match_score = 0.45 * t_score + 0.25 * e_score + 0.15 * d_score + 0.15 * r_score

    features = CandidateFeatures(
        text_similarity=t_score,
        entity_overlap=e_score,
        date_score=d_score,
        resolution_score=r_score,
        entities_a=entities_a,
        entities_b=entities_b,
    )
    return MatchCandidate(market_a=market_a, market_b=market_b, match_score=match_score, features=features)


def _entity_date_bucket(market: Market) -> Set[Tuple[str, str]]:
    entities = extract_entities(market)
    day = market.end_time.date().isoformat()
    return {(e, day) for e in entities if len(e) > 2}


def stage_one_candidates(markets_a: Iterable[Market], markets_b: Iterable[Market], max_per_market: int = 20) -> Dict[str, List[Market]]:
    index: Dict[Tuple[str, str], List[Market]] = defaultdict(list)
    for market in markets_b:
        if market.market_type != "binary":
            continue
        for key in _entity_date_bucket(market):
            index[key].append(market)

    candidates: Dict[str, List[Market]] = {}
    for market in markets_a:
        if market.market_type != "binary":
            continue
        pool: Set[Market] = set()
        for key in _entity_date_bucket(market):
            pool.update(index.get(key, []))

        ranked = sorted(pool, key=lambda m: text_similarity(market.title, m.title), reverse=True)
        candidates[market.market_id] = ranked[:max_per_market]
    return candidates


def stage_two_matches(
    markets_a: Iterable[Market],
    candidate_map: Dict[str, List[Market]],
    alert_threshold: float,
    review_threshold: float,
) -> Tuple[List[MatchCandidate], List[MatchCandidate]]:
    alerts: List[MatchCandidate] = []
    review: List[MatchCandidate] = []

    for market_a in markets_a:
        for market_b in candidate_map.get(market_a.market_id, []):
            candidate = score_candidate(market_a, market_b)
            if candidate.match_score >= alert_threshold:
                alerts.append(candidate)
            elif candidate.match_score >= review_threshold:
                review.append(MatchCandidate(**{**candidate.__dict__, "review_only": True}))

    alerts.sort(key=lambda c: c.match_score, reverse=True)
    review.sort(key=lambda c: c.match_score, reverse=True)
    return alerts, review
