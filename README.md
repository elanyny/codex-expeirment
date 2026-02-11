# Cross-Venue Prediction Market Arb Scanner (MVP)

Python bot for matching related binary markets across venues and sending **high-confidence, net-profitable** arbitrage alerts to Telegram.

## What this includes

- Two-stage matching pipeline:
  - **Stage 1**: candidate generation (cheap filters)
  - **Stage 2**: weighted confidence scoring
- Outcome alignment with negation handling
- Net edge calculation with conservative buffers (fees/slippage/latency/gas)
- Alert throttling (cooldown and minimum edge delta)
- Telegram integration
- Live market fetchers for:
  - Polymarket (Gamma API)
  - Manifold (public API)
- Unit tests for matching and edge math

## Default refresh rate

This bot defaults to **15 seconds** (`SCAN_INTERVAL_SECONDS=15`), which is a practical balance for most setups.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run demo mode (no external APIs):

```bash
python -m src.main --demo --dry-run --once
```

Run live mode once (fetch real markets):

```bash
python -m src.main --dry-run --once
```

Run live continuously:

```bash
python -m src.main
```

## Real launch checklist (Telegram + live markets)

1. Create a Telegram bot via BotFather and get `TELEGRAM_BOT_TOKEN`.
2. Get your `TELEGRAM_CHAT_ID`.
3. Export environment variables:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export SCAN_INTERVAL_SECONDS=15
export MARKET_FETCH_LIMIT=250
export MATCH_ALERT_THRESHOLD=0.82
export MATCH_REVIEW_THRESHOLD=0.70
export MIN_NET_EDGE=0.015
export EDGE_BUFFER=0.010
export MIN_LIQUIDITY=100
```

4. Sanity check in dry-run first:

```bash
python -m src.main --dry-run --once
```

5. Start live notifications:

```bash
python -m src.main
```

## Configuration

Set env vars (or edit defaults in `src/config.py`):

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `DRY_RUN`
- `SCAN_INTERVAL_SECONDS` (default: 15)
- `MATCH_ALERT_THRESHOLD` (default: 0.82)
- `MATCH_REVIEW_THRESHOLD` (default: 0.70)
- `MIN_NET_EDGE` (default: 0.015)
- `EDGE_BUFFER` (default: 0.010)
- `MIN_LIQUIDITY` (default: 100)
- `PAIR_COOLDOWN_SECONDS` (default: 300)
- `EDGE_IMPROVEMENT_TRIGGER` (default: 0.005)
- `POLYMARKET_API_URL` (default: `https://gamma-api.polymarket.com/markets`)
- `MANIFOLD_API_URL` (default: `https://api.manifold.markets/v0/markets`)
- `MARKET_FETCH_LIMIT` (default: 250)

## Project structure

- `src/models.py` — data models (`Market`, `MatchCandidate`, `ArbOpportunity`, etc.)
- `src/matching.py` — stage 1 + stage 2 matching logic
- `src/alignment.py` — YES/NO alignment and inversion detection
- `src/arb.py` — edge calculation after costs and buffer
- `src/alerts.py` — Telegram notifier + alert payload formatter
- `src/venues.py` — live market fetchers/adapters
- `src/scanner.py` — scanner loop and cooldown/throttle policy
- `src/main.py` — CLI entrypoint
- `tests/` — unit tests

## Applying to real conditions (recommended tuning)

- Start conservative:
  - `MATCH_ALERT_THRESHOLD=0.85`
  - `MIN_NET_EDGE=0.02`
  - `EDGE_BUFFER=0.012`
- Raise liquidity floor if you get unfillable alerts:
  - `MIN_LIQUIDITY=200` or higher
- Keep a review workflow:
  - monitor review list outputs before enabling full alerting
- Add per-market blacklist persistence if certain recurring false matches appear

## Notes on productionizing

- Replace heuristic text matcher with embeddings.
- Improve entity extraction with NER + canonical entity dictionaries.
- Add orderbook-level sizing for more accurate executable edge.
- Persist matched pairs and false positives to a DB.
