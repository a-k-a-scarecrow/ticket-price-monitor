"""Tracks the last known price per (event, site) pair.

Persisted to state.json and committed back to the repo by the GitHub
Actions workflow after each run. Serves two purposes: the web app reads
it to show each watchlist entry's current price, and main.py compares
against it to only notify when a price actually changes — not every
hour it stays the same.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Listing

DEFAULT_STATE_PATH = Path(__file__).resolve().parents[2] / "state.json"


def load_state(path: Path = DEFAULT_STATE_PATH) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: dict, path: Path = DEFAULT_STATE_PATH) -> None:
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def get_last_price(state: dict, event_key: str, site: str) -> float | None:
    record = state.get(event_key, {}).get(site)
    return record.get("price") if record else None


def set_price(state: dict, event_key: str, site: str, listing: Listing, updated_at: str) -> None:
    state.setdefault(event_key, {})[site] = {
        "price": listing.price,
        "currency": listing.currency,
        "url": listing.url,
        "quantity": listing.quantity,
        "updated_at": updated_at,
    }
