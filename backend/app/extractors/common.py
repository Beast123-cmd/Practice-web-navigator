from __future__ import annotations
from playwright.async_api import Locator

async def safe_text(loc: Locator | None, timeout: int = 2000) -> str | None:
    """
    Get textContent from a locator safely with a short timeout.
    Returns None if the node is missing or times out.
    """
    if not loc:
        return None
    try:
        return await loc.text_content(timeout=timeout)
    except Exception:
        return None

async def safe_attr(loc: Locator | None, name: str, timeout: int = 2000) -> str | None:
    """
    Get a specific attribute from a locator safely with a short timeout.
    Returns None if the node is missing or times out.
    """
    if not loc:
        return None
    try:
        return await loc.get_attribute(name, timeout=timeout)
    except Exception:
        return None
