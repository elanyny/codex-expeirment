from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Market:
    venue: str
    market_id: str
    title: str
    end_time: datetime
    market_type: str = "binary"
    resolution_rules: str = ""
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    yes_liquidity: float = 0.0
    no_liquidity: float = 0.0


@dataclass(frozen=True)
class CandidateFeatures:
    text_similarity: float
    entity_overlap: float
    date_score: float
    resolution_score: float
    entities_a: Set[str]
    entities_b: Set[str]


@dataclass(frozen=True)
class MatchCandidate:
    market_a: Market
    market_b: Market
    match_score: float
    features: CandidateFeatures
    review_only: bool = False


@dataclass(frozen=True)
class CostModel:
    fee_a: float = 0.0
    fee_b: float = 0.0
    slippage_a: float = 0.002
    slippage_b: float = 0.002
    gas: float = 0.0
    latency_buffer: float = 0.005


@dataclass(frozen=True)
class ArbLeg:
    venue: str
    side: str
    price: float
    max_size: float


@dataclass(frozen=True)
class ArbOpportunity:
    candidate: MatchCandidate
    leg_a: ArbLeg
    leg_b: ArbLeg
    effective_sum: float
    net_edge: float
    aligned: bool
    alignment_reason: str
    timestamp: datetime


@dataclass
class ScannerState:
    last_alert_time: Dict[Tuple[str, str], datetime] = field(default_factory=dict)
    last_alert_edge: Dict[Tuple[str, str], float] = field(default_factory=dict)
