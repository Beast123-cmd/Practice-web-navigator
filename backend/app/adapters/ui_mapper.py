from __future__ import annotations
from typing import List
from ..schemas import Product, UIProduct
from ..services.utils import format_inr, specs_from_title, specs_from_attrs


def _build_specs(p: Product) -> List[str]:
    """
    Compose short, human-readable specs with this priority:
      1) Category-aware attrs (if extractor filled p.attrs)
      2) Heuristics from title text
    """
    specs: List[str] = []

    # 1) From structured attributes (category-agnostic + category-specific)
    specs.extend(specs_from_attrs(p.category or "", p.attrs or {}))

    # 2) From title heuristics (fallback/augmentation)
    if len(specs) < 4:  # keep concise; top 4–6 bullets
        more = specs_from_title(p.title)
        for m in more:
            if m not in specs:
                specs.append(m)
            if len(specs) >= 6:
                break

    return specs[:6]


def map_for_ui(p: Product) -> UIProduct:
    """
    Convert internal Product → UIProduct your React pages use.
    """
    return UIProduct(
        name=p.title,
        price=format_inr(p.price),          # "₹45,000" or "—"
        rating=p.rating,
        specifications=_build_specs(p),
        link=p.url,
        image=p.image,
        source=p.source,
        reviewCount=p.review_count,
        rawTitle=p.title,
        category=p.category,
    )


def map_many(products: List[Product]) -> List[UIProduct]:
    return [map_for_ui(p) for p in products]
