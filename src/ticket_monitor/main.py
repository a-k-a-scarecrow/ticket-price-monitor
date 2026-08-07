"""Entry point: scans every watchlist entry across sources, tracks each
one's current price, and alerts on any price change. Run hourly by
GitHub Actions, or manually with `python -m ticket_monitor.main`.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from . import notify, state as state_module
from .config import ConfigError, load_settings, load_watchlist
from .sources import seatgeek, stubhub, ticketmaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> int:
    settings = load_settings()

    if not settings.ticketmaster_api_key and not settings.seatgeek_client_id:
        logger.error(
            "No source API keys configured (TICKETMASTER_API_KEY / SEATGEEK_CLIENT_ID). "
            "Nothing to scan — see README for setup."
        )
        return 1

    try:
        watchlist = load_watchlist()
    except ConfigError as exc:
        logger.error("Failed to load watchlist: %s", exc)
        return 1

    if not watchlist:
        logger.info("Watchlist is empty — nothing to do.")
        return 0

    state = state_module.load_state()
    state_changed = False
    scan_time = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for entry in watchlist:
        webhook_url = entry.discord_webhook_url or settings.discord_webhook_url
        if not webhook_url:
            logger.error(
                "No Discord webhook for '%s' (set DISCORD_WEBHOOK_URL or add "
                "discord_webhook_url to this watchlist entry) — skipping.",
                entry.artist,
            )
            continue

        logger.info("Scanning %s in %s on %s (max $%.2f)", entry.artist, entry.city, entry.date, entry.max_price)

        listings = []
        try:
            listings.extend(ticketmaster.fetch_listings(entry, settings))
        except Exception:
            logger.exception("Ticketmaster lookup crashed for %s", entry.artist)
        try:
            listings.extend(seatgeek.fetch_listings(entry, settings))
        except Exception:
            logger.exception("SeatGeek lookup crashed for %s", entry.artist)
        try:
            listings.extend(stubhub.fetch_listings(entry))
        except Exception:
            logger.exception("StubHub lookup crashed for %s", entry.artist)

        for listing in listings:
            last_price = state_module.get_last_price(state, entry.key, listing.site)
            if last_price is not None and last_price == listing.price:
                continue  # no change since the last scan

            notify.send_price_alert(entry, listing, webhook_url, stubhub.search_url(entry), previous_price=last_price)
            state_module.set_price(state, entry.key, listing.site, listing, scan_time)
            state_changed = True

    if state_changed:
        state_module.save_state(state)

    return 0


if __name__ == "__main__":
    sys.exit(run())
