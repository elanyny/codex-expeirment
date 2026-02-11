from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    scan_interval_seconds: int = int(os.getenv("SCAN_INTERVAL_SECONDS", "15"))

    match_alert_threshold: float = float(os.getenv("MATCH_ALERT_THRESHOLD", "0.82"))
    match_review_threshold: float = float(os.getenv("MATCH_REVIEW_THRESHOLD", "0.70"))

    min_net_edge: float = float(os.getenv("MIN_NET_EDGE", "0.015"))
    edge_buffer: float = float(os.getenv("EDGE_BUFFER", "0.010"))
    min_liquidity: float = float(os.getenv("MIN_LIQUIDITY", "100"))

    pair_cooldown_seconds: int = int(os.getenv("PAIR_COOLDOWN_SECONDS", "300"))
    edge_improvement_trigger: float = float(os.getenv("EDGE_IMPROVEMENT_TRIGGER", "0.005"))

    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"

    polymarket_api_url: str = os.getenv("POLYMARKET_API_URL", "https://gamma-api.polymarket.com/markets")
    manifold_api_url: str = os.getenv("MANIFOLD_API_URL", "https://api.manifold.markets/v0/markets")
    market_fetch_limit: int = int(os.getenv("MARKET_FETCH_LIMIT", "250"))
