from __future__ import annotations

from datetime import datetime
from typing import Optional

from .alignment import align_outcomes
from .models import ArbLeg, ArbOpportunity, CostModel, MatchCandidate


def _effective_price(price: float, fee: float, slippage: float) -> float:
    return price + fee + slippage


def evaluate_opportunity(candidate: MatchCandidate, costs: CostModel, edge_buffer: float) -> Optional[ArbOpportunity]:
    a = candidate.market_a
    b = candidate.market_b

    aligned, relation, reason = align_outcomes(a, b)
    if not aligned:
        return None

    if a.yes_price is None or a.no_price is None or b.yes_price is None or b.no_price is None:
        return None

    if relation == "same":
        leg_a = ArbLeg(venue=a.venue, side="YES", price=a.yes_price, max_size=a.yes_liquidity)
        leg_b = ArbLeg(venue=b.venue, side="NO", price=b.no_price, max_size=b.no_liquidity)
        eff_sum = _effective_price(a.yes_price, costs.fee_a, costs.slippage_a) + _effective_price(
            b.no_price, costs.fee_b, costs.slippage_b
        )
    else:
        leg_a = ArbLeg(venue=a.venue, side="YES", price=a.yes_price, max_size=a.yes_liquidity)
        leg_b = ArbLeg(venue=b.venue, side="YES", price=b.yes_price, max_size=b.yes_liquidity)
        eff_sum = _effective_price(a.yes_price, costs.fee_a, costs.slippage_a) + _effective_price(
            b.yes_price, costs.fee_b, costs.slippage_b
        )

    eff_sum += costs.gas + costs.latency_buffer
    net_edge = 1.0 - edge_buffer - eff_sum

    return ArbOpportunity(
        candidate=candidate,
        leg_a=leg_a,
        leg_b=leg_b,
        effective_sum=eff_sum,
        net_edge=net_edge,
        aligned=True,
        alignment_reason=reason,
        timestamp=datetime.utcnow(),
    )
