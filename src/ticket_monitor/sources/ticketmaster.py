"""Ticketmaster Discovery API — official, free, documented.

Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

Note: Ticketmaster exposes a price *range* per event (min/max), not
individual ticket listings, so quantity is always None here.
"""

from __future__ import annotations

import logging

import requests

from ..config import Settings, WatchEntry
from ..models import EventSummary, Listing

logger = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
TIMEOUT_SECONDS = 15


def fetch_listings(entry: WatchEntry, settings: Settings) -> list[Listing]:
    if not settings.ticketmaster_api_key:
        logger.info("Skipping Ticketmaster: TICKETMASTER_API_KEY not set")
        return []

    params = {
        "apikey": settings.ticketmaster_api_key,
        "keyword": entry.artist,
        "city": entry.city,
        "startDateTime": f"{entry.date}T00:00:00Z",
        "endDateTime": f"{entry.date}T23:59:59Z",
        "size": 20,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Ticketmaster request failed for %s: %s", entry.artist, exc)
        return []

    data = resp.json()
    events = data.get("_embedded", {}).get("events", [])

    listings: list[Listing] = []
    for event in events:
        local_date = event.get("dates", {}).get("start", {}).get("localDate")
        if local_date != entry.date:
            continue

        url = event.get("url")
        for price_range in event.get("priceRanges", []):
            min_price = price_range.get("min")
            if min_price is None or url is None:
                continue
            listings.append(
                Listing(
                    site="Ticketmaster",
                    price=float(min_price),
                    currency=price_range.get("currency", "USD"),
                    url=url,
                    quantity=None,
                )
            )

    return listings


def search_events(city: str, api_key: str, keyword: str | None = None, size: int = 20) -> list[EventSummary]:
    """Browse upcoming music events in a city, without knowing the artist.

    Used by the CLI search command and (indirectly, via a user-supplied key
    in the browser) the web app's "Browse concerts" feature.
    """
    params = {
        "apikey": api_key,
        "city": city,
        "classificationName": "music",
        "sort": "date,asc",
        "size": size,
    }
    if keyword:
        params["keyword"] = keyword

    resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()

    data = resp.json()
    events = data.get("_embedded", {}).get("events", [])

    results: list[EventSummary] = []
    for event in events:
        attractions = event.get("_embedded", {}).get("attractions", [])
        artist = attractions[0]["name"] if attractions else event.get("name", "Unknown artist")

        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0].get("name", "Unknown venue") if venues else "Unknown venue"

        local_date = event.get("dates", {}).get("start", {}).get("localDate", "Unknown date")
        url = event.get("url", "")

        price_ranges = event.get("priceRanges", [])
        min_price = min((pr["min"] for pr in price_ranges if "min" in pr), default=None)
        max_price = max((pr["max"] for pr in price_ranges if "max" in pr), default=None)
        currency = price_ranges[0].get("currency") if price_ranges else None

        results.append(
            EventSummary(
                artist=artist,
                venue=venue,
                city=city,
                date=local_date,
                url=url,
                min_price=min_price,
                max_price=max_price,
                currency=currency,
            )
        )

    return results
