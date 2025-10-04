from __future__ import annotations
from typing import List, Dict
from ..schemas import Product
from ..services.scoring import rank_products


async def run(
    products: List[Product],
    constraints: Dict,
    query: str,
    k: int,
) -> List[Product]:
    """
    Ranker agent:
      - de-duplicates near-identical listings
      - scores each product (title similarity, price vs budget, rating/reviews, attribute match)
      - returns top-K results
    """
    return rank_products(products, constraints, query, k)
