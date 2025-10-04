from __future__ import annotations
import math
from typing import Dict, List, Tuple, Any
from .utils import similar
from ..schemas import Product


# -----------------------------
# Attribute match scoring
# -----------------------------
def _normalize_str(x: Any) -> str:
    return str(x).strip().lower() if x is not None else ""


def _in_list(val: str | None, arr: List[str] | None) -> bool:
    if not val or not arr:
        return False
    v = _normalize_str(val)
    return any(_normalize_str(a) == v for a in arr)


def _any_overlap(arr1: List[str] | None, arr2: List[str] | None) -> bool:
    if not arr1 or not arr2:
        return False
    s1 = {_normalize_str(a) for a in arr1}
    s2 = {_normalize_str(a) for a in arr2}
    return len(s1 & s2) > 0


def attribute_match_score(p: Product, constraints: Dict[str, Any]) -> float:
    """
    Compare Product.attrs against parser constraints["filters"] in a category-agnostic way.
    Return a 0..1 score (soft, not a hard filter).
    """
    if not constraints:
        return 0.0

    filters: Dict[str, Any] = constraints.get("filters") or {}
    if not filters:
        return 0.0

    attrs = p.attrs or {}
    score = 0.0
    max_pts = 0.0

    # Brand
    brands = filters.get("brand")
    if isinstance(brands, list):
        max_pts += 1.0
        prod_brands = attrs.get("brand") or attrs.get("maker") or []
        if isinstance(prod_brands, list) and _any_overlap(prod_brands, brands):
            score += 1.0
        else:
            # fallback: title contains a brand token
            name = p.title.lower()
            if any(b.lower() in name for b in brands):
                score += 0.8

    # Color
    colors = filters.get("color")
    if isinstance(colors, list):
        max_pts += 0.5
        prod_colors = attrs.get("color")
        if isinstance(prod_colors, list) and _any_overlap(prod_colors, colors):
            score += 0.5

    # Material
    materials = filters.get("material")
    if isinstance(materials, list):
        max_pts += 0.6
        prod_mat = attrs.get("material")
        if isinstance(prod_mat, list) and _any_overlap(prod_mat, materials):
            score += 0.6

    # Footwear sizes
    for key, pts in (("size_uk", 0.5), ("size_us", 0.5), ("size_eu", 0.5)):
        want = _normalize_str(filters.get(key))
        got = _normalize_str(attrs.get(key))
        if want:
            max_pts += pts
            if want and got and want == got:
                score += pts

    # Capacity (litres) — allow small tolerance
    cap_want = filters.get("capacity_l")
    cap_got = attrs.get("capacity_l")
    if cap_want:
        max_pts += 0.6
        try:
            want = float(cap_want)
            got = float(cap_got) if cap_got is not None else None
            if got is not None and abs(got - want) <= 0.5:
                score += 0.6
        except Exception:
            pass

    # Electronics: RAM, Storage, Battery — string compare is fine (parsed from title)
    if filters.get("ram_gb"):
        max_pts += 0.6
        if _normalize_str(filters.get("ram_gb")) == _normalize_str(attrs.get("ram_gb")):
            score += 0.6

    if filters.get("storage_tb"):
        max_pts += 0.6
        if _normalize_str(filters.get("storage_tb")) == _normalize_str(attrs.get("storage_tb")):
            score += 0.6

    if filters.get("storage_gb"):
        max_pts += 0.6
        if _normalize_str(filters.get("storage_gb")) == _normalize_str(attrs.get("storage_gb")):
            score += 0.6

    if filters.get("battery_mah"):
        max_pts += 0.6
        if _normalize_str(filters.get("battery_mah")) == _normalize_str(attrs.get("battery_mah")):
            score += 0.6

    # Normalize to 0..1 (avoid div by zero)
    if max_pts <= 0:
        return 0.0
    return max(0.0, min(1.0, score / max_pts))


# -----------------------------
# Core scoring / ranking
# -----------------------------
def score_product(p: Product, constraints: Dict[str, Any], query: str) -> float:
    """
    Combine:
      - title/query similarity
      - price vs budget
      - rating + review volume
      - attribute match vs user filters (brand/color/material/size/ram/storage/etc.)
      - loose keyword hits (from parser)
    Return a score in ~0..1.5 (we clamp later).
    """
    budget = constraints.get("budget")
    kws: List[str] = constraints.get("keywords", [])

    # 1) Title similarity (0..1)
    sim = similar(p.title.lower(), query.lower()) / 100.0

    # 2) Price fitness relative to budget (0..1)
    if p.price and budget:
        if p.price <= budget:
            price_score = 1.0 - (p.price / max(budget, 1)) * 0.6  # cheaper is better
            price_score = max(0.25, price_score)                 # floor for under-budget items
        else:
            # over budget: soft penalty; don't zero-out (user may accept slight over)
            price_score = max(0.05, 1.0 - (p.price - budget) / max(budget, 1) * 1.2)
    else:
        price_score = 0.45

    # 3) Social proof
    rating_score = (p.rating or 0) / 5.0
    review_boost = math.tanh((p.review_count or 0) / 600.0)  # saturates ~1 around 600+

    # 4) Attribute match vs filters (0..1)
    attr_score = attribute_match_score(p, constraints)

    # 5) Keyword bonus: if user mentioned tokens (e.g., waterproof, induction)
    kw_bonus = 0.0
    title_l = p.title.lower()
    for kw in kws:
        if isinstance(kw, str) and kw in title_l:
            kw_bonus += 0.03
    kw_bonus = min(0.15, kw_bonus)

    # Weighted total
    total = (
        0.30 * sim +
        0.30 * price_score +
        0.18 * rating_score +
        0.10 * review_boost +
        0.12 * attr_score +
        kw_bonus
    )
    return float(max(0.0, min(1.6, total)))


def dedup(products: List[Product]) -> List[Product]:
    """
    Remove near-duplicates across sites using fuzzy title similarity.
    """
    out: List[Product] = []
    for p in products:
        if not any(similar(p.title, q.title) > 88 for q in out):
            out.append(p)
    return out


def rank_products(products: List[Product], constraints: Dict[str, Any], query: str, k: int) -> List[Product]:
    """
    De-duplicate, score, and return top-K products.
    """
    items = dedup(products)
    scored: List[Tuple[float, Product]] = [(score_product(p, constraints, query), p) for p in items]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in scored[:k]]
