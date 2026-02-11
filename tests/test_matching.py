from datetime import datetime, timedelta

from src.matching import date_score, normalize_text, score_candidate
from src.models import Market


def _mk(title: str, end_days: int, rules: str = "") -> Market:
    return Market(
        venue="A",
        market_id=title,
        title=title,
        end_time=datetime.utcnow() + timedelta(days=end_days),
        resolution_rules=rules,
        yes_price=0.4,
        no_price=0.6,
    )


def test_normalize_text_synonyms():
    text = "Will CPI be above 3 percent?"
    normalized = normalize_text(text)
    assert "inflation" in normalized
    assert "%" in normalized


def test_date_score_buckets():
    now = datetime.utcnow()
    assert date_score(now, now) == 1.0
    assert date_score(now, now + timedelta(days=2)) == 0.7
    assert date_score(now, now + timedelta(days=6)) == 0.3
    assert date_score(now, now + timedelta(days=10)) == 0.0


def test_score_candidate_high_for_similar_markets():
    a = _mk("Will US inflation be above 3.0% in March 2026?", 30, "Uses CPI print")
    b = _mk("US CPI inflation over 3 percent in Mar 2026?", 31, "Resolved by CPI print")
    c = score_candidate(a, b)
    assert c.match_score > 0.6
