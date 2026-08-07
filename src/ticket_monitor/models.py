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
