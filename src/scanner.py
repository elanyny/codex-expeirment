from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

from .alerts import TelegramNotifier, format_alert, format_review
from .arb import evaluate_opportunity
from .config import Settings
from .matching import stage_one_candidates, stage_two_matches
from .models import CostModel, Market, ScannerState


class Scanner:
    def __init__(self, settings: Settings, notifier: TelegramNotifier, costs: CostModel):
        self.settings = settings
        self.notifier = notifier
        self.costs = costs
        self.state = ScannerState()

    def _pair_key(self, a: Market, b: Market) -> tuple[str, str]:
        return tuple(sorted([f"{a.venue}:{a.market_id}", f"{b.venue}:{b.market_id}"]))

    def _should_alert(self, key: tuple[str, str], edge: float, now: datetime) -> bool:
        last_time = self.state.last_alert_time.get(key)
        last_edge = self.state.last_alert_edge.get(key, -1.0)

        if last_time is None:
            return True

        cooldown_passed = now - last_time >= timedelta(seconds=self.settings.pair_cooldown_seconds)
        edge_improved = edge - last_edge >= self.settings.edge_improvement_trigger
        return cooldown_passed or edge_improved

    def run_once(self, venue_a_markets: Sequence[Market], venue_b_markets: Sequence[Market]) -> None:
        candidate_map = stage_one_candidates(venue_a_markets, venue_b_markets)
        alert_matches, review_matches = stage_two_matches(
            venue_a_markets,
            candidate_map,
            alert_threshold=self.settings.match_alert_threshold,
            review_threshold=self.settings.match_review_threshold,
        )

        now = datetime.utcnow()
        sent = 0
        for match in alert_matches:
            opp = evaluate_opportunity(match, self.costs, self.settings.edge_buffer)
            if not opp:
                continue

            min_liquidity_ok = min(opp.leg_a.max_size, opp.leg_b.max_size) >= self.settings.min_liquidity
            edge_ok = opp.net_edge >= self.settings.min_net_edge
            if not (min_liquidity_ok and edge_ok):
                continue

            key = self._pair_key(match.market_a, match.market_b)
            if self._should_alert(key, opp.net_edge, now):
                self.notifier.send(format_alert(opp))
                self.state.last_alert_time[key] = now
                self.state.last_alert_edge[key] = opp.net_edge
                sent += 1

        if review_matches:
            self.notifier.send(format_review(review_matches[:10]))

        print(f"scan complete at {now.isoformat()}Z | alerts={sent} | review={len(review_matches)}")
