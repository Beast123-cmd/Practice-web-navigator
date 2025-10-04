from __future__ import annotations
import asyncio
from typing import List, Dict, Any, Callable
from playwright.async_api import async_playwright

from ..schemas import Product
from ..extractors import amazon, flipkart


# Map site id → extractor function
_EXTRACTORS: Dict[str, Callable[..., Any]] = {
    "amazon": amazon.extract,
    "flipkart": flipkart.extract,
}


async def navigate_and_extract(
    query: str,
    sites: List[str],
    constraints: Dict[str, Any] | None = None,
) -> List[Product]:
    """
    Launches a real Chromium browser (headless), opens a new page per site,
    navigates to each site's search results, and returns unified Product rows.
    """
    async with async_playwright() as p:
        # 1) Launch headless Chromium
        browser = await p.chromium.launch(headless=True)

        # 2) New browser context (per run) — set locale & sane defaults
        context = await browser.new_context(
            locale="en-IN",
            viewport={"width": 1366, "height": 900},
        )

        results: List[Product] = []

        async def run_site(site: str) -> List[Product]:
            """
            Create an isolated page per site and delegate to the site's extractor.
            """
            page = await context.new_page()
            # Reasonable timeouts per page
            page.set_default_timeout(10_000)
            try:
                extractor = _EXTRACTORS.get(site)
                if not extractor:
                    return []

                # Call extractor with graceful fallback if it doesn't support constraints (compat)
                try:
                    return await extractor(page, query, constraints=constraints)
                except TypeError:
                    return await extractor(page, query)

            except Exception:
                # Soft-fail per site; don't break the whole run
                return []
            finally:
                await page.close()

        try:
            # 3) Run all requested sites concurrently
            tasks = [run_site(s) for s in sites]
            chunks = await asyncio.gather(*tasks, return_exceptions=True)

            # 4) Merge successful chunks
            for ch in chunks:
                if isinstance(ch, Exception):
                    continue
                results.extend(ch)

        finally:
            # 5) Cleanup
            await context.close()
            await browser.close()

        return results
