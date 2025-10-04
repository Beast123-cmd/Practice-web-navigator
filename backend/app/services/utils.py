from __future__ import annotations
import re
from typing import Dict, Any, List
from rapidfuzz import fuzz

# -----------------------------
# Basic parsers / formatters
# -----------------------------
PRICE_RX  = re.compile(r"(?:₹|INR\s*)\s*([0-9,]+)")
DIGIT_RX  = re.compile(r"([0-9][0-9,]*)")
RATING_RX = re.compile(r"([0-9]+(?:\.[0-9])?)\s*out\s*of\s*5", re.I)

def parse_price(text: str | None) -> float | None:
    if not text:
        return None
    m = PRICE_RX.search(text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except Exception:
            pass
    m2 = DIGIT_RX.search(text or "")
    if m2:
        try:
            return float(m2.group(1).replace(",", ""))
        except Exception:
            return None
    return None

def parse_int(text: str | None) -> int | None:
    if not text:
        return None
    m = DIGIT_RX.search(text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except Exception:
            return None
    return None

def parse_rating(text: str | None) -> float | None:
    if not text:
        return None
    try:
        m = RATING_RX.search(text)
        if m:
            return float(m.group(1))
        return float(text)
    except Exception:
        return None

def clean_title(t: str | None) -> str:
    return re.sub(r"\s+", " ", (t or "").strip())

def similar(a: str, b: str) -> float:
    return float(fuzz.token_set_ratio(a, b))  # 0..100

def format_inr(n: float | int | None) -> str:
    if n is None:
        return "—"
    v = int(round(float(n)))
    return f"₹{v:,}"


# -----------------------------
# Category-agnostic attribute parsing
# (works for electronics, shoes, utensils, bags, etc.)
# -----------------------------
# Reusable regex helpers
def _rx_num(unit: str) -> re.Pattern:
    return re.compile(rf"\b(\d+(?:\.\d+)?)\s*{unit}\b", re.I)

RX_RAM_GB       = re.compile(r"\b(\d{1,2})\s*GB(?:\s*RAM)?\b", re.I)
RX_STORAGE_GB   = re.compile(r"\b(\d{2,4})\s*GB\b", re.I)
RX_STORAGE_TB   = re.compile(r"\b(\d(?:\.\d)?)\s*TB\b", re.I)
RX_BATTERY_MAH  = re.compile(r"\b(\d{3,5})\s*mAh\b", re.I)
RX_REFRESH_HZ   = re.compile(r"\b(60|90|120|144|165|240)\s*Hz\b", re.I)
RX_SCREEN_IN    = re.compile(r"\b(\d{2}(?:\.\d)?)\s*inch(?:es)?\b", re.I)
RX_SIZE_UK      = re.compile(r"\buk\s*(\d{1,2})\b", re.I)
RX_SIZE_US      = re.compile(r"\bus\s*(\d{1,2})\b", re.I)
RX_SIZE_EU      = re.compile(r"\beu\s*(\d{1,2})\b", re.I)
RX_CAP_L        = _rx_num("l")
RX_WATT         = _rx_num("w")
RX_LITRE        = re.compile(r"\b(\d{1,3})(?:\.?\d*)\s*(?:L|Litre|Liters|Litres)\b", re.I)

# Simple token sets for heuristics
CPU_TOKENS = [
    "i3", "i5", "i7", "i9",
    "ryzen 3", "ryzen 5", "ryzen 7", "ryzen 9",
    "m1", "m2", "m3", "m4",
    "celeron", "pentium", "mediatek", "snapdragon", "exynos", "dimensity", "helio",
]
PANEL_TOKENS = ["oled", "amoled", "ips", "tn", "va", "fhd", "full hd", "qhd", "uhd", "4k", "touch"]
MATERIAL_TOKENS = [
    "leather","synthetic","mesh","cotton","polyester","nylon","canvas","suede",
    "stainless","stainless steel","steel","cast iron","aluminium","aluminum",
    "ceramic","glass","bamboo","wood","nonstick","non-stick",
]
COLOR_TOKENS = [
    "black","white","silver","grey","gray","red","blue","green","yellow","pink",
    "purple","orange","gold","rose","beige","brown","maroon","navy","teal",
]

def _first(rx: re.Pattern, text: str) -> str | None:
    m = rx.search(text)
    return m.group(1) if m else None

def _tokens_present(text: str, vocab: List[str]) -> List[str]:
    t = text.lower()
    out: List[str] = []
    for v in vocab:
        if v in t:
            out.append(v)
    return out

def parse_generic_attrs_from_title(title: str) -> Dict[str, Any]:
    """
    Extract a flexible set of attributes from ANY product title.
    This is intentionally broad and low-risk: it won't throw if nothing is found.
    """
    t = title.lower()
    attrs: Dict[str, Any] = {}

    # Electronics-y (optional for any category)
    ram = _first(RX_RAM_GB, t)
    if ram: attrs["ram_gb"] = ram
    storage_tb = _first(RX_STORAGE_TB, t)
    storage_gb = None if storage_tb else _first(RX_STORAGE_GB, t)
    if storage_tb: attrs["storage_tb"] = storage_tb
    if storage_gb: attrs["storage_gb"] = storage_gb
    battery = _first(RX_BATTERY_MAH, t)
    if battery: attrs["battery_mah"] = battery
    refresh = _first(RX_REFRESH_HZ, t)
    if refresh: attrs["refresh_hz"] = refresh
    screen = _first(RX_SCREEN_IN, t)
    if screen: attrs["screen_in"] = screen

    # Apparel / shoes sizing (optional)
    size_uk = _first(RX_SIZE_UK, t)
    size_us = _first(RX_SIZE_US, t)
    size_eu = _first(RX_SIZE_EU, t)
    if size_uk: attrs["size_uk"] = size_uk
    if size_us: attrs["size_us"] = size_us
    if size_eu: attrs["size_eu"] = size_eu

    # Home / kitchen capacity & power
    lit = _first(RX_LITRE, t) or _first(RX_CAP_L, t)
    if lit: attrs["capacity_l"] = lit
    watts = _first(RX_WATT, t)
    if watts: attrs["watt"] = watts

    # Materials, Colors, CPU/Panels (token-based)
    cpus = _tokens_present(t, CPU_TOKENS)
    if cpus: attrs["cpu"] = list(dict.fromkeys(cpus))
    panels = _tokens_present(t, PANEL_TOKENS)
    if panels: attrs["panel"] = list(dict.fromkeys(panels))
    materials = _tokens_present(t, MATERIAL_TOKENS)
    if materials: attrs["material"] = list(dict.fromkeys(materials))
    colors = _tokens_present(t, COLOR_TOKENS)
    if colors: attrs["color"] = list(dict.fromkeys(colors))

    return attrs


# -----------------------------
# Turning attrs into short UI specs
# -----------------------------
def _short(label: str, val: Any) -> str:
    if isinstance(val, list):
        val = ", ".join(map(str, val[:3]))
    return f"{label}: {val}"

def specs_from_attrs(category: str, attrs: Dict[str, Any]) -> List[str]:
    """
    Convert parsed attrs into compact bullet specs. Category is only a hint to order fields.
    """
    if not attrs:
        return []

    order_generic = [
        ("brand", "Brand"), ("cpu", "CPU"), ("ram_gb", "RAM"),
        ("storage_tb", "Storage TB"), ("storage_gb", "Storage GB"),
        ("battery_mah", "Battery"), ("refresh_hz", "Refresh"),
        ("screen_in", "Screen"), ("color", "Color"), ("material", "Material"),
        ("capacity_l", "Capacity"), ("watt", "Watt"), ("size_uk", "UK"),
        ("size_us", "US"), ("size_eu", "EU"), ("panel", "Panel"),
    ]

    # Light reordering by category
    if category == "fashion":
        order = [("size_uk","UK"),("size_us","US"),("size_eu","EU"),("material","Material"),
                 ("color","Color"),("brand","Brand")]
        # then fallback to generic
        seen = {k for k,_ in order}
        order += [(k,l) for k,l in order_generic if k not in seen]
    elif category in ("home-kitchen", "appliances"):
        order = [("capacity_l","Capacity"),("material","Material"),("watt","Watt"),
                 ("brand","Brand"),("color","Color")]
        seen = {k for k,_ in order}
        order += [(k,l) for k,l in order_generic if k not in seen]
    else:
        order = order_generic

    specs: List[str] = []
    for key, label in order:
        if key in attrs and attrs[key] not in (None, "", []):
            specs.append(_short(label, attrs[key]))
        if len(specs) >= 6:
            break
    return specs

# Fallback heuristic when attrs are sparse
def specs_from_title(title: str) -> List[str]:
    attrs = parse_generic_attrs_from_title(title)
    return specs_from_attrs("", attrs)
