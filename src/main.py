from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta

from .alerts import TelegramNotifier
from .config import Settings
from .models import CostModel, Market
from .scanner import Scanner
from .venues import fetch_manifold_markets, fetch_polymarket_markets


def demo_markets():
    now = datetime.utcnow()
    venue_a = [
        Market(
            venue="Polymarket",
            market_id="pm-1",
            title="Will US inflation be above 3.0% in March 2026?",
            end_time=now + timedelta(days=30),
            resolution_rules="Resolved using official CPI release for March 2026.",
            yes_price=0.44,
            no_price=0.56,
            yes_liquidity=500,
            no_liquidity=500,
        ),
        Market(
            venue="Polymarket",
            market_id="pm-2",
            title="Will Candidate X win the 2026 election?",
            end_time=now + timedelta(days=200),
            resolution_rules="Winner by certified national vote.",
            yes_price=0.61,
            no_price=0.39,
            yes_liquidity=350,
            no_liquidity=350,
        ),
    ]
    venue_b = [
        Market(
            venue="Manifold",
            market_id="mf-1",
            title="US CPI inflation over 3 percent in Mar 2026?",
            end_time=now + timedelta(days=29),
            resolution_rules="Uses BLS CPI publication for March 2026.",
            yes_price=0.43,
            no_price=0.57,
            yes_liquidity=450,
            no_liquidity=450,
        ),
        Market(
            venue="Manifold",
            market_id="mf-2",
            title="Will Candidate X fail to win the 2026 election?",
            end_time=now + timedelta(days=201),
            resolution_rules="Uses certified election result.",
            yes_price=0.37,
            no_price=0.63,
            yes_liquidity=250,
            no_liquidity=250,
        ),
    ]
    return venue_a, venue_b


def load_live_markets(settings: Settings) -> tuple[list[Market], list[Market]]:
    polymarket = fetch_polymarket_markets(settings.polymarket_api_url, settings.market_fetch_limit)
    manifold = fetch_manifold_markets(settings.manifold_api_url, settings.market_fetch_limit)
    print(f"loaded markets: polymarket={len(polymarket)} manifold={len(manifold)}")
    return polymarket, manifold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Use built-in demo markets")
    parser.add_argument("--dry-run", action="store_true", help="Print alerts instead of sending Telegram messages")
    parser.add_argument("--once", action="store_true", help="Run one scan and exit")
    args = parser.parse_args()

    settings = Settings()
    notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id, dry_run=args.dry_run or settings.dry_run)
    scanner = Scanner(settings, notifier, costs=CostModel())

    def load_markets() -> tuple[list[Market], list[Market]]:
        if args.demo:
            return demo_markets()
        return load_live_markets(settings)

    if args.once:
        venue_a, venue_b = load_markets()
        scanner.run_once(venue_a, venue_b)
        return

    while True:
        venue_a, venue_b = load_markets()
        scanner.run_once(venue_a, venue_b)
        time.sleep(settings.scan_interval_seconds)


if __name__ == "__main__":
    main()
