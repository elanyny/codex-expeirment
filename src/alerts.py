from __future__ import annotations

import json
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import ArbOpportunity


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, dry_run: bool = False):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.dry_run = dry_run

    def send(self, message: str) -> None:
        if self.dry_run:
            print("[DRY RUN TELEGRAM]\n" + message)
            return
        if not self.bot_token or not self.chat_id:
            raise ValueError("Missing Telegram credentials")

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": message}).encode("utf-8")
        req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"Telegram API error: {resp.status}")
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"Telegram request failed: {exc}") from exc


def format_alert(opportunity: ArbOpportunity) -> str:
    c = opportunity.candidate
    common = sorted(c.features.entities_a & c.features.entities_b)
    top_entities = ", ".join(common[:8]) if common else "none"

    return (
        "🚨 Arb Candidate\n"
        f"A: [{c.market_a.venue}] {c.market_a.title}\n"
        f"B: [{c.market_b.venue}] {c.market_b.title}\n"
        f"Match score: {c.match_score:.3f} (text={c.features.text_similarity:.2f}, entities={c.features.entity_overlap:.2f}, date={c.features.date_score:.2f}, rules={c.features.resolution_score:.2f})\n"
        f"Entities: {top_entities}\n"
        "Legs:\n"
        f"- {opportunity.leg_a.venue} BUY {opportunity.leg_a.side} @ {opportunity.leg_a.price:.3f}, size <= {opportunity.leg_a.max_size:.2f}\n"
        f"- {opportunity.leg_b.venue} BUY {opportunity.leg_b.side} @ {opportunity.leg_b.price:.3f}, size <= {opportunity.leg_b.max_size:.2f}\n"
        f"Effective sum: {opportunity.effective_sum:.4f}\n"
        f"Net edge after costs: {opportunity.net_edge * 100:.2f}%\n"
        f"Snapshot: {opportunity.timestamp.isoformat()}Z\n"
        "Checklist: same resolution source, same end time, wording not inverted."
    )


def format_review(candidates: Iterable) -> str:
    lines = ["📝 Match Review List"]
    for c in candidates:
        lines.append(f"- {c.match_score:.3f}: {c.market_a.title}  <->  {c.market_b.title}")
    return "\n".join(lines)
