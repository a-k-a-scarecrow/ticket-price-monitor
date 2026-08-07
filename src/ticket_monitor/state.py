"""Tracks the last price we alerted on for each (event, site) pair.

Persisted to state.json and committed back to the repo by the GitHub
Actions workflow after each run, so re-notification only happens when a
price actually changes — not every hour it stays the same.
"""

from __future__ import annotations

import json
from pathlib import Path

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


def last_notified_price(state: dict, event_key: str, site: str) -> float | None:
    return state.get(event_key, {}).get(site)


def set_notified_price(state: dict, event_key: str, site: str, price: float) -> None:
    state.setdefault(event_key, {})[site] = price
