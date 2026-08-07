"""Sends price-drop alerts to a Discord channel via webhook.

Discord webhooks need no bot/OAuth setup: create one under a channel's
Integrations settings and paste the URL into DISCORD_WEBHOOK_URL (or a
per-entry override in watchlist.yaml). Free, unlimited, native push
notifications on mobile + desktop via the Discord app.
"""

from __future__ import annotations

import logging

import requests

from .config import WatchEntry
from .models import Listing

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 10


def send_price_alert(entry: WatchEntry, listing: Listing, webhook_url: str, stubhub_search_url: str) -> None:
    quantity_str = f"{listing.quantity} available" if listing.quantity is not None else "quantity not reported"

    content = (
        f"🎟️ **{entry.artist}** — {entry.city} on {entry.date}\n"
        f"**{listing.site}** has tickets at **${listing.price:,.2f} {listing.currency}** "
        f"(your max: ${entry.max_price:,.2f}) — {quantity_str}\n"
        f"{listing.url}\n"
        f"-# Also check StubHub manually: {stubhub_search_url}"
    )

    try:
        resp = requests.post(webhook_url, json={"content": content}, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to send Discord notification for %s: %s", entry.artist, exc)


def send_error_alert(webhook_url: str, message: str) -> None:
    try:
        resp = requests.post(webhook_url, json={"content": f"⚠️ Ticket monitor error: {message}"}, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to send Discord error alert: %s", exc)
