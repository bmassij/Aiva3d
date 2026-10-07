"""Margin policy."""

from __future__ import annotations


def sale_price_from_cost(cost_price: float, margin_percent: float) -> float:
    """Sale price with margin on top of cost (markup on cost)."""
    if cost_price <= 0:
        return 0.0
    return round(cost_price * (1.0 + margin_percent / 100.0), 2)
