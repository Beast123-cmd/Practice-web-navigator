from __future__ import annotations
from typing import List, Dict, Any
from ..schemas import Product


async def run(
    products: List[Product],
    constraints: Dict[str, Any] | None = None,
) -> List[Product]:
    """
    Extractor agent (category-agnostic).

    In this build, site extractors (amazon/flipkart) already return normalized
    Product rows with parsed attrs from titles. This agent is kept as a
    consolidation/normalization hook:
      - ensure category is set (fallback from parser constraints)
      - future: enrich attrs from HTML blocks, spec tables, or PDP pages
      - future: resolve conflicts across multiple listings for the same item
    """
    if constraints and constraints.get("category"):
        cat = constraints["category"]
        for p in products:
            if not p.category:
                p.category = cat
    return products
