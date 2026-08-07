"""Sends price-change alerts to a Discord channel via webhook.

Discord webhooks need no bot/OAuth setup: create one under a channel's
Integrations settings and paste the URL into DISCORD_WEBHOOK_URL (or a
per-entry override in watchlist.yaml). Free, unlimited, native push
notifications on mobile + desktop via the Discord app.

Notifies on every price change, not just drops below max_price — the
message always states the current price against your max so it's clear
whether it's actually a good deal.
"""

from __future__ import annotations

import logging

import requests

from .config import WatchEntry
from .models import Listing

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 10


def send_price_alert(
    entry: WatchEntry,
    listing: Listing,
    webhook_url: str,
    stubhub_search_url: str,
    previous_price: float | None = None,
) -> None:
    quantity_str = f"{listing.quantity} available" if listing.quantity is not None else "quantity not reported"
    within_budget = listing.price <= entry.max_price

    if previous_price is None:
        change_str = "first price seen"
    elif listing.price < previous_price:
        change_str = f"down from ${previous_price:,.2f}"
    elif listing.price > previous_price:
        change_str = f"up from ${previous_price:,.2f}"
    else:
        change_str = "unchanged"

    status_emoji = "✅" if within_budget else "📊"
    budget_str = "at or below your max!" if within_budget else "still above your max"

    content = (
        f"{status_emoji} **{entry.artist}** — {entry.city} on {entry.date}\n"
        f"**{listing.site}**: **${listing.price:,.2f} {listing.currency}** ({change_str}) — "
        f"{budget_str} (your max: ${entry.max_price:,.2f}) — {quantity_str}\n"
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
