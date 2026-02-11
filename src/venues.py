from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import urlopen

from .models import Market


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        # epoch seconds
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)

    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def _json_get(url: str) -> Any:
    try:
        with urlopen(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        print(f"warning: failed to fetch {url}: {exc}")
        return []


def _parse_polymarket_yes_no(item: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    # observed variants:
    # - outcomePrices: '["0.42","0.58"]'
    # - outcome_prices: [0.42,0.58]
    # - yes_price / no_price
    yes = item.get("yes_price")
    no = item.get("no_price")
    if yes is not None and no is not None:
        return _safe_float(yes, None), _safe_float(no, None)

    prices = item.get("outcomePrices", item.get("outcome_prices"))
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except json.JSONDecodeError:
            prices = None

    if isinstance(prices, list) and len(prices) >= 2:
        return _safe_float(prices[0], None), _safe_float(prices[1], None)

    last = item.get("lastTradePrice", item.get("last_trade_price"))
    if last is not None:
        yes_guess = _safe_float(last, None)
        if yes_guess is not None:
            return yes_guess, max(0.0, 1.0 - yes_guess)
    return None, None


def fetch_polymarket_markets(base_url: str = "https://gamma-api.polymarket.com/markets", limit: int = 250) -> List[Market]:
    query = urlencode({"closed": "false", "limit": str(limit)})
    data = _json_get(f"{base_url}?{query}")
    items: Iterable[Dict[str, Any]] = data if isinstance(data, list) else []

    markets: List[Market] = []
    for item in items:
        market_type = str(item.get("outcomeType", item.get("outcome_type", "binary"))).lower()
        if market_type != "binary":
            continue

        end_time = _parse_datetime(item.get("endDate", item.get("end_time", item.get("closeTime"))))
        if end_time is None:
            continue

        title = str(item.get("question", item.get("title", ""))).strip()
        if not title:
            continue

        market_id = str(item.get("id", item.get("conditionId", title)))
        yes_price, no_price = _parse_polymarket_yes_no(item)
        liquidity = _safe_float(item.get("liquidity", item.get("volume", 0.0)), 0.0)

        markets.append(
            Market(
                venue="Polymarket",
                market_id=market_id,
                title=title,
                end_time=end_time,
                market_type="binary",
                resolution_rules=str(item.get("description", item.get("resolution", ""))),
                yes_price=yes_price,
                no_price=no_price,
                yes_liquidity=liquidity,
                no_liquidity=liquidity,
            )
        )
    return markets


def fetch_manifold_markets(base_url: str = "https://api.manifold.markets/v0/markets", limit: int = 250) -> List[Market]:
    query = urlencode({"limit": str(limit)})
    data = _json_get(f"{base_url}?{query}")
    items: Iterable[Dict[str, Any]] = data if isinstance(data, list) else []

    markets: List[Market] = []
    for item in items:
        if str(item.get("outcomeType", "")).upper() != "BINARY":
            continue

        close_time_ms = item.get("closeTime")
        if close_time_ms is None:
            continue
        end_time = _parse_datetime(float(close_time_ms) / 1000.0)
        if end_time is None:
            continue

        title = str(item.get("question", "")).strip()
        if not title:
            continue

        prob = item.get("probability")
        yes_price = _safe_float(prob, None)
        no_price = None if yes_price is None else max(0.0, 1.0 - yes_price)

        liquidity = _safe_float(item.get("totalLiquidity", item.get("volume", 0.0)), 0.0)
        market_id = str(item.get("id", title))

        markets.append(
            Market(
                venue="Manifold",
                market_id=market_id,
                title=title,
                end_time=end_time,
                market_type="binary",
                resolution_rules=str(item.get("description", "")),
                yes_price=yes_price,
                no_price=no_price,
                yes_liquidity=liquidity,
                no_liquidity=liquidity,
            )
        )
    return markets
