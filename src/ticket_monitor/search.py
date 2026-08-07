"""Browse upcoming concerts by city, when you don't know the exact artist.

    python -m ticket_monitor.search --city "Toronto"
    python -m ticket_monitor.search --city "Toronto" --keyword "rock"
    python -m ticket_monitor.search --city "Toronto" --month 2026-09
    python -m ticket_monitor.search --city "Toronto" --date 2026-09-16

Prints matches from Ticketmaster so you can find an artist/date to add to
config/watchlist.yaml (by hand, via the web app, or by asking Claude).
"""

from __future__ import annotations

import argparse
import calendar
import sys

import requests

from .config import load_settings
from .sources.ticketmaster import search_events


def month_bounds(month: str) -> tuple[str, str]:
    """'2026-09' -> ('2026-09-01', '2026-09-30')."""
    year_str, month_str = month.split("-")
    year, mon = int(year_str), int(month_str)
    last_day = calendar.monthrange(year, mon)[1]
    return f"{year:04d}-{mon:02d}-01", f"{year:04d}-{mon:02d}-{last_day:02d}"


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
    parser.add_argument("--size", type=int, default=200, help="results per page (default 200, Ticketmaster's max)")
    parser.add_argument("--page", type=int, default=0, help="page number, if a search has more results than fit on one page (default 0)")
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument("--month", help="restrict to one month, YYYY-MM (e.g. 2026-09)")
    date_group.add_argument("--date", help="restrict to one day, YYYY-MM-DD")
    args = parser.parse_args(argv)

    settings = load_settings()
    if not settings.ticketmaster_api_key:
        print("TICKETMASTER_API_KEY is not set in your environment.", file=sys.stderr)
        return 1

    start_date = end_date = None
    if args.month:
        start_date, end_date = month_bounds(args.month)
    elif args.date:
        start_date = end_date = args.date

    try:
        results, has_more = search_events(
            args.city,
            settings.ticketmaster_api_key,
            keyword=args.keyword,
            size=args.size,
            page=args.page,
            start_date=start_date,
            end_date=end_date,
        )
    except requests.RequestException as exc:
        print(f"Ticketmaster request failed: {exc}", file=sys.stderr)
        return 1

    if not results:
        print(f"No upcoming music events found in {args.city} (page {args.page}).")
        return 0

    for r in results:
        price = format_price(r.min_price, r.max_price, r.currency)
        print(f"{r.date}  {r.artist}  —  {r.venue}, {r.city}  ({price})")
        print(f"    {r.url}")

    if has_more:
        print(f"\nMore results available — rerun with --page {args.page + 1} to see the next page.")

    return 0


if __name__ == "__main__":
    sys.exit(run())
