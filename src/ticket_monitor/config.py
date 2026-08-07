"""Loads the watchlist file and required environment/secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WATCHLIST_PATH = REPO_ROOT / "config" / "watchlist.yaml"


class ConfigError(RuntimeError):
    pass


@dataclass
class WatchEntry:
    artist: str
    city: str
    date: str
    max_price: float
    discord_webhook_url: str | None = None

    @property
    def key(self) -> str:
        return f"{self.artist}|{self.city}|{self.date}".lower()


@dataclass
class Settings:
    ticketmaster_api_key: str | None
    seatgeek_client_id: str | None
    discord_webhook_url: str | None


def load_watchlist(path: Path = DEFAULT_WATCHLIST_PATH) -> list[WatchEntry]:
    if not path.exists():
        raise ConfigError(f"Watchlist file not found: {path}")

    raw = yaml.safe_load(path.read_text()) or []
    if not isinstance(raw, list):
        raise ConfigError("watchlist.yaml must be a list of entries")

    entries: list[WatchEntry] = []
    for i, item in enumerate(raw):
        missing = [f for f in ("artist", "city", "date", "max_price") if f not in item]
        if missing:
            raise ConfigError(f"watchlist entry #{i} missing fields: {missing}")
        entries.append(
            WatchEntry(
                artist=str(item["artist"]),
                city=str(item["city"]),
                date=str(item["date"]),
                max_price=float(item["max_price"]),
                discord_webhook_url=item.get("discord_webhook_url"),
            )
        )
    return entries


def load_settings() -> Settings:
    return Settings(
        ticketmaster_api_key=os.environ.get("TICKETMASTER_API_KEY"),
        seatgeek_client_id=os.environ.get("SEATGEEK_CLIENT_ID"),
        discord_webhook_url=os.environ.get("DISCORD_WEBHOOK_URL"),
    )
