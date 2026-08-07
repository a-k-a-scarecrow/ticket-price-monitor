"""StubHub has no public API, and (as verified during development) its
search endpoints are protected by AWS WAF bot-detection — plain HTTP
requests get blocked (seen as either a 202 "challenge" response or a
403) with no usable page content.

We deliberately do NOT attempt to defeat that challenge (e.g. via a
headless browser). This module tries a plain, honest request; if it's
blocked (which is the current, consistent outcome), it logs that once
and returns no listings rather than failing the whole run.

Because of this, StubHub is not part of the automated price scan today.
`search_url()` below is used instead to hand you a direct search link in
every notification, so you can check StubHub yourself in one tap.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import requests

from ..config import WatchEntry
from ..models import Listing

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
_warned = False


def search_url(entry: WatchEntry) -> str:
    query = quote_plus(f"{entry.artist} {entry.city}")
    return f"https://www.stubhub.com/secure/search?q={query}"


def fetch_listings(entry: WatchEntry) -> list[Listing]:
    global _warned
    try:
        resp = requests.get(search_url(entry), timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.info("StubHub request failed for %s: %s", entry.artist, exc)
        return []

    if resp.status_code != 200:
        if not _warned:
            logger.info(
                "StubHub is blocking automated requests (got HTTP %s, likely "
                "bot-detection). Skipping StubHub price data; a direct search "
                "link is included in notifications instead.",
                resp.status_code,
            )
            _warned = True
        return []

    # If StubHub ever stops blocking plain requests, there is intentionally
    # no parsing logic here yet — the page is a JS-rendered SPA and would
    # need real (non-evasive) access, e.g. an official API, to parse reliably.
    return []
