"""Browse upcoming concerts by city, when you don't know the exact artist.

    python -m ticket_monitor.search --city "Toronto"
    python -m ticket_monitor.search --city "Toronto" --keyword "rock"

Prints matches from Ticketmaster so you can find an artist/date to add to
config/watchlist.yaml (by hand, via the web app, or by asking Claude).
"""

from __future__ import annotations

import argparse
import sys

import requests

from .config import load_settings
from .sources.ticketmaster import search_events


def format_price(min_price: float | None, max_price: float | None, currency: str | None) -> str:
    if min_price is None:
        return "price unknown"
    if max_price is not None and max_price != min_price:
        return f"${min_price:,.0f}-${max_price:,.0f} {currency or ''}".strip()
    return f"from ${min_price:,.0f} {currency or ''}".strip()


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Browse upcoming concerts in a city via Ticketmaster")
    parser.add_argument("--city", required=True, help='e.g. "Toronto"')
    parser.add_argument("--keyword", help="optional extra filter, e.g. a genre or partial artist name")
    parser.add_argument("--size", type=int, default=20, help="max results (default 20)")
    args = parser.parse_args(argv)

    settings = load_settings()
    if not settings.ticketmaster_api_key:
        print("TICKETMASTER_API_KEY is not set in your environment.", file=sys.stderr)
        return 1

    try:
        results = search_events(args.city, settings.ticketmaster_api_key, keyword=args.keyword, size=args.size)
    except requests.RequestException as exc:
        print(f"Ticketmaster request failed: {exc}", file=sys.stderr)
        return 1

    if not results:
        print(f"No upcoming music events found in {args.city}.")
        return 0

    for r in results:
        price = format_price(r.min_price, r.max_price, r.currency)
        print(f"{r.date}  {r.artist}  —  {r.venue}, {r.city}  ({price})")
        print(f"    {r.url}")

    return 0


if __name__ == "__main__":
    sys.exit(run())
