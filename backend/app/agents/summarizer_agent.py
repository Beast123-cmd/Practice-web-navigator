from __future__ import annotations
from typing import Dict, List, Optional
from ..schemas import Product


def _min_price(products: List[Product]) -> Optional[Product]:
    return min((p for p in products if p.price is not None), key=lambda x: x.price, default=None)

def _max_rating(products: List[Product]) -> Optional[Product]:
    return max((p for p in products if p.rating is not None), key=lambda x: x.rating, default=None)

def _fmt_inr(n: float | int | None) -> str:
    if n is None:
        return "—"
    try:
        return f"₹{int(round(float(n))):,}"
    except Exception:
        return "—"


def summarize(products: List[Product], constraints: Dict, query: str) -> str:
    """
    Short, category-agnostic summary string for the UI header.
    Mentions budget if present and highlights cheapest / highest-rated items.
    """
    if not products:
        return "I couldn’t find good matches. Try tweaking the budget or adding a brand/material/size."

    budget = constraints.get("budget")
    category = constraints.get("category")

    # Headline
    head_parts = []
    head_parts.append(f"Top {len(products)} picks")
    if category:
        head_parts.append(f"in {category}")
    head_parts.append(f"for: “{query}”")
    if budget:
        head_parts.append(f"(near budget {_fmt_inr(budget)})")
    headline = " ".join(head_parts) + "."

    # Highlights
    cheapest = _min_price(products)
    highest_rated = _max_rating(products)

    lines = [headline]

    if cheapest:
        lines.append(f"Lowest price: {cheapest.title[:72]} — {_fmt_inr(cheapest.price)} [{cheapest.source}].")

    if highest_rated and highest_rated.rating is not None:
        lines.append(
            f"Highest rated: {highest_rated.title[:72]} — {highest_rated.rating}/5"
            + (f", {_fmt_inr(highest_rated.price)}" if highest_rated.price else "")
            + f" [{highest_rated.source}]."
        )

    return " \n".join(lines)


async def run(products: List[Product], constraints: Dict, query: str) -> str:
    return summarize(products, constraints, query)
