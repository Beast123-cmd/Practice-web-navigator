from __future__ import annotations
from typing import List, Dict, Any
from ..schemas import Product
from ..services.browser import navigate_and_extract


def _augment_query(query: str, constraints: Dict[str, Any] | None) -> str:
    """
    Build a category-agnostic query that works across sites.
    We lightly append useful tokens (category, brands) without overfitting.
    """
    if not constraints:
        return query

    tokens: list[str] = []

    # Add inferred category (electronics, fashion, home-kitchen, etc.) if present
    category = constraints.get("category")
    if isinstance(category, str) and category:
        tokens.append(category)

    # Add brand hints if any
    filters = constraints.get("filters") or {}
    brands = filters.get("brand") or []
    if isinstance(brands, list):
        tokens.extend([b for b in brands if isinstance(b, str)])

    # Keep it simple and robust for generic search pages
    if tokens:
        return f"{query} " + " ".join(tokens)
    return query


async def run(
    query: str,
    sites: List[str],
    constraints: Dict[str, Any] | None = None,
) -> List[Product]:
    """
    Navigator agent:
      - Augments the free-text query with light hints (category/brand)
      - Delegates real-time scraping to Playwright via services.browser
      - Returns a unified list[Product] from all requested sites
    """
    q = _augment_query(query, constraints)
    # Pass constraints through so the browser/extractors can optionally use them
    return await navigate_and_extract(q, sites, constraints=constraints)
