from datetime import datetime

from src.arb import evaluate_opportunity
from src.models import CostModel, Market, MatchCandidate, CandidateFeatures


def test_evaluate_opportunity_positive_edge():
    a = Market(
        venue="A",
        market_id="1",
        title="Will X happen?",
        end_time=datetime.utcnow(),
        yes_price=0.40,
        no_price=0.60,
        yes_liquidity=200,
        no_liquidity=200,
    )
    b = Market(
        venue="B",
        market_id="2",
        title="Will X happen?",
        end_time=datetime.utcnow(),
        yes_price=0.62,
        no_price=0.38,
        yes_liquidity=200,
        no_liquidity=200,
    )
    candidate = MatchCandidate(
        market_a=a,
        market_b=b,
        match_score=0.9,
        features=CandidateFeatures(0.9, 0.8, 1.0, 0.8, {"x"}, {"x"}),
    )
    opp = evaluate_opportunity(candidate, CostModel(fee_a=0, fee_b=0, slippage_a=0, slippage_b=0, gas=0, latency_buffer=0), edge_buffer=0)
    assert opp is not None
    assert opp.net_edge > 0
