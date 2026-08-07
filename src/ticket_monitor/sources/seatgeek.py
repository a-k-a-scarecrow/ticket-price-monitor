"""SeatGeek Platform API — official, free, documented.

Docs: https://platform.seatgeek.com/

A client_id alone (no client_secret) is sufficient for read-only GET
requests like event search. SeatGeek aggregates resale marketplaces, so
`stats.listing_count` gives a genuine ticket-availability count.
"""

from __future__ import annotations

import logging

import requests

from ..config import Settings, WatchEntry
from ..models import Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://api.seatgeek.com/2/events"
TIMEOUT_SECONDS = 15


def fetch_listings(entry: WatchEntry, settings: Settings) -> list[Listing]:
    if not settings.seatgeek_client_id:
        logger.info("Skipping SeatGeek: SEATGEEK_CLIENT_ID not set")
        return []

    params = {
        "client_id": settings.seatgeek_client_id,
        "q": entry.artist,
        "venue.city": entry.city,
        "datetime_local.gte": f"{entry.date}T00:00:00",
        "datetime_local.lte": f"{entry.date}T23:59:59",
        "per_page": 20,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("SeatGeek request failed for %s: %s", entry.artist, exc)
        return []

    data = resp.json()
    events = data.get("events", [])

    listings: list[Listing] = []
    for event in events:
        stats = event.get("stats", {})
        lowest_price = stats.get("lowest_price")
        url = event.get("url")
        if lowest_price is None or url is None:
            continue
        listings.append(
            Listing(
                site="SeatGeek",
                price=float(lowest_price),
                currency="USD",
                url=url,
                quantity=stats.get("listing_count"),
            )
        )

    return listings
