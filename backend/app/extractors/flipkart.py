from __future__ import annotations
from typing import List, Dict, Any
from urllib.parse import quote_plus
from playwright.async_api import Page

from ..schemas import Product
from ..services.utils import (
    parse_price,
    parse_int,
    parse_rating,
    clean_title,
    parse_generic_attrs_from_title,  # category-agnostic attrs
)
from .common import safe_text, safe_attr


async def _search_url(query: str) -> str:
    # Generic search keeps us resilient across categories (mobiles, shoes, utensils, bags, etc.)
    return f"https://www.flipkart.com/search?q={quote_plus(query)}"


async def extract(
    page: Page,
    query: str,
    constraints: Dict[str, Any] | None = None,
) -> List[Product]:
    """
    Category-agnostic Flipkart extractor.
    Scrapes the search page, normalizes to Product objects with flexible attrs.
    """
    url = await _search_url(query)
    await page.goto(url, wait_until="domcontentloaded")

    # Flipkart often uses one of these containers depending on category
    await page.wait_for_selector("div._1AtVbE, div._1YokD2", timeout=12000)

    budget = None
    category = None
    if constraints:
        budget = constraints.get("budget")
        category = constraints.get("category")

    results: List[Product] = []

    # Try primary card containers
    cards = await page.query_selector_all("div._1AtVbE")
    if not cards:
        # Fallback to alternate layout (e.g., electronics grid cards)
        cards = await page.query_selector_all("div._2kHMtA, a._1fQZEK, a.s1Q9rs")

    for c in cards[:40]:
        # ---- Title ----
        # Try multiple selectors across categories/layouts
        title = None
        for sel in ["div._4rR01T", "a._1fQZEK", "a.s1Q9rs", "div.KzDlHZ", "a.IRpwTa"]:
            node_text = await safe_text(c.query_selector(sel))
            if node_text:
                title = node_text
                break

        # ---- Link ----
        link = None
        for sel in ["a._1fQZEK", "a.s1Q9rs", "a._2UzuFa", "a.IRpwTa"]:
            href = await safe_attr(c.query_selector(sel), "href")
            if href:
                link = href
                break

        # ---- Price ----
        price_text = None
        for sel in ["div._30jeq3._1_WHN1", "div._30jeq3", "div.Nx9bqj.CxhGGd"]:
            pt = await safe_text(c.query_selector(sel))
            if pt:
                price_text = pt
                break

        # ---- Rating & Reviews ----
        rating_text = await safe_text(c.query_selector("div._3LWZlK"))
        # Example: "1,234 Ratings & 123 Reviews"
        reviews_text = await safe_text(c.query_selector("span._2_R_DZ"))
        # Some verticals use different class for ratings count:
        if not reviews_text:
            reviews_text = await safe_text(c.query_selector("span.Wphh3N"))

        # ---- Image ----
        img = None
        for sel in ["img[loading]", "img._396cs4", "img.DByuf4"]:
            src = await safe_attr(c.query_selector(sel), "src")
            if src:
                img = src
                break

        if not title or not link:
            continue

        title_clean = clean_title(title)
        price_val = parse_price(price_text)
        rating_val = parse_rating(rating_text)
        review_cnt = parse_int(reviews_text)

        # Optional early budget pruning (keep some headroom for variants)
        if budget and price_val and price_val > budget * 2.2:
            continue

        attrs = parse_generic_attrs_from_title(title_clean)

        href = ("https://www.flipkart.com" + link) if link.startswith("/") else link

        results.append(
            Product(
                title=title_clean,
                price=price_val,
                rating=rating_val,
                review_count=review_cnt,
                url=href,
                image=img,
                source="flipkart",
                category=category,
                attrs=attrs,
                raw={
                    "price_text": price_text,
                    "rating_text": rating_text,
                    "reviews_text": reviews_text,
                },
            )
        )

    return results
