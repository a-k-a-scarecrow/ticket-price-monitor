"""Shared data shapes passed between source modules and the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Listing:
    site: str
    price: float
    currency: str
    url: str
    quantity: int | None  # None when the source API doesn't expose inventory counts


@dataclass
class EventSummary:
    """A browsable event result, e.g. from searching Ticketmaster by city."""

    artist: str
    venue: str
    city: str
    date: str
    url: str
    min_price: float | None
    max_price: float | None
    currency: str | None
