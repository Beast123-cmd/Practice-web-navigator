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
    parse_generic_attrs_from_title,  # will parse attrs for ANY category
)
from .common import safe_text, safe_attr


async def _search_url(query: str) -> str:
    # Keep it simple & robust: generic search page
    # (Avoid brittle filter params; ranking/budget filtering happens later.)
    return f"https://www.amazon.in/s?k={quote_plus(query)}"


async def extract(
    page: Page,
    query: str,
    constraints: Dict[str, Any] | None = None,
) -> List[Product]:
    """
    Category-agnostic Amazon extractor.
    Returns normalized Product rows (title, price, rating, reviews, url, image, source)
    with optional `category` and `attrs` parsed from title.
    """
    url = await _search_url(query)
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_selector("div.s-main-slot", timeout=12000)

    cards = await page.query_selector_all(
        "div.s-main-slot div[data-component-type='s-search-result']"
    )

    budget = None
    category = None
    if constraints:
        budget = constraints.get("budget")
        category = constraints.get("category")

    results: List[Product] = []
    for c in cards[:36]:
        title = await safe_text(c.locator("h2 a span"))
        link = await safe_attr(c.locator("h2 a"), "href")
        price_text = await safe_text(c.locator(".a-price .a-offscreen").first)
        rating_text = await safe_text(c.locator("span.a-icon-alt").first)
        reviews_text = await safe_text(
            c.locator("span[aria-label*='ratings'], span[aria-label*='rating']").first
        )
        img = await safe_attr(c.locator("img.s-image"), "src")

        if not title or not link:
            continue

        title_clean = clean_title(title)
        price_val = parse_price(price_text)
        rating_val = parse_rating(rating_text)
        review_cnt = parse_int(reviews_text)

        # Optional early budget skip to reduce noise (ranking still re-checks)
        if budget and price_val and price_val > budget * 2.2:
            # Heuristic guard: keep within ~2.2x budget to allow near-misses/variants
            continue

        # Parse generic attributes from title (works for laptops, shoes, utensils, etc.)
        attrs = parse_generic_attrs_from_title(title_clean)

        # Build absolute product URL
        href = ("https://www.amazon.in" + link) if link.startswith("/") else link

        results.append(
            Product(
                title=title_clean,
                price=price_val,
                rating=rating_val,
                review_count=review_cnt,
                url=href,
                image=img,
                source="amazon",
                category=category,   # keep parser-inferred category if any
                attrs=attrs,         # flexible attributes dict
                raw={
                    "price_text": price_text,
                    "rating_text": rating_text,
                    "reviews_text": reviews_text,
                },
            )
        )

    return results
