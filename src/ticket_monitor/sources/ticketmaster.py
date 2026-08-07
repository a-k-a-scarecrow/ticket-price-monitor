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


def search_events(
    city: str,
    api_key: str,
    keyword: str | None = None,
    size: int = 200,
    page: int = 0,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[EventSummary], bool]:
    """Browse upcoming music events in a city, without knowing the artist.

    start_date/end_date (YYYY-MM-DD, inclusive) narrow results to a specific
    day or month; omit both to just get the soonest upcoming events.

    Ticketmaster paginates (200 is its max page size), so a single call may
    not cover an entire month for a busy city. Returns (events, has_more) —
    call again with page+1 when has_more is True to get the rest.

    Used by the CLI search command and (indirectly, via a user-supplied key
    in the browser) the web app's "Browse concerts" feature.
    """
    params = {
        "apikey": api_key,
        "city": city,
        "classificationName": "music",
        "sort": "date,asc",
        "size": size,
        "page": page,
    }
    if keyword:
        params["keyword"] = keyword
    if start_date:
        params["startDateTime"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["endDateTime"] = f"{end_date}T23:59:59Z"

    resp = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()

    data = resp.json()
    events = data.get("_embedded", {}).get("events", [])

    page_info = data.get("page", {})
    has_more = (page_info.get("number", 0) + 1) < page_info.get("totalPages", 0)

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

    if start_date or end_date:
        # Results are sorted ascending by date. If this page's last event is
        # already past end_date, every later page only has later dates too —
        # nothing more to find for this range, regardless of how many raw
        # pages Ticketmaster reports.
        if end_date and results and results[-1].date != "Unknown date" and results[-1].date > end_date:
            has_more = False

        # Ticketmaster's date filter is loose: multi-date listings (season
        # passes, recurring classes) get included if their overall range
        # merely overlaps the window, not just events strictly inside it.
        # Filter client-side for a result set that actually matches.
        results = [
            r for r in results
            if r.date != "Unknown date"
            and (not start_date or r.date >= start_date)
            and (not end_date or r.date <= end_date)
        ]

    return results, has_more
