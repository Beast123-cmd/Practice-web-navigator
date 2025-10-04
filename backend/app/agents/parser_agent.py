from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple


# -----------------------------
# Dictionaries / lexicons
# -----------------------------
CATEGORY_KEYWORDS = {
    "electronics": [
        "laptop", "notebook", "ultrabook", "macbook",
        "mobile", "smartphone", "phone", "earbuds", "headphones", "camera",
        "tablet", "ipad", "monitor", "tv", "television", "router", "printer",
        "smartwatch", "wearable", "ssd", "hdd", "pendrive", "power bank",
    ],
    "fashion": [
        "shoes", "sneakers", "sandals", "heels", "loafers",
        "t-shirt", "shirt", "jeans", "kurta", "saree", "hoodie", "jacket",
        "backpack", "bag", "duffle", "wallet", "belt",
    ],
    "home-kitchen": [
        "utensils", "cookware", "pan", "kadhai", "frying pan", "pressure cooker",
        "bottle", "flask", "mug", "tiffin", "lunch box", "container", "plate",
        "nonstick", "non-stick", "induction", "stainless", "cutlery",
    ],
    "appliances": [
        "fridge", "refrigerator", "washing machine", "ac", "air conditioner",
        "microwave", "oven", "chimney", "cooler", "geyser", "water heater",
    ],
    "sports": [
        "football", "cricket bat", "bat", "ball", "badminton", "racket",
        "dumbbell", "treadmill", "yoga", "gym bag",
    ],
    "beauty": [
        "shampoo", "conditioner", "lotion", "cream", "facewash", "makeup",
        "lipstick", "perfume", "deodorant", "serum",
    ],
}

# Common brands across categories (non-exhaustive; easy to extend)
BRANDS = [
    # Electronics
    "apple","samsung","oneplus","xiaomi","redmi","realme","oppo","vivo",
    "dell","hp","lenovo","asus","acer","msi","lg","sony","boat","jbl","noise",
    "canon","nikon","sandisk","seagate","wd","western digital",
    # Fashion / bags
    "nike","adidas","puma","reebok","bata","woodland","zara","h&m","levis",
    "allen solly","us polo","wildcraft","american tourister","skybag","safari",
    # Home & kitchen
    "prestige","pigeon","hawkins","milton","cello","borosil","butterfly","vinod",
    # Appliances
    "whirlpool","bosch","ifb","voltas","panasonic","hitachi","haier","godrej",
]

COLORS = [
    "black","white","silver","grey","gray","red","blue","green","yellow","pink",
    "purple","orange","gold","rose","beige","brown","maroon","navy","teal",
]

MATERIALS = [
    "leather","synthetic","mesh","cotton","polyester","nylon","canvas","suede",
    "stainless","stainless steel","steel","cast iron","aluminium","aluminum",
    "ceramic","glass","bamboo","wood",
]


# -----------------------------
# Helpers
# -----------------------------
def _rx_num(unit: str) -> re.Pattern:
    return re.compile(rf"\b(\d+(?:\.\d+)?)\s*{unit}\b", re.I)

RX_UNDER_K     = re.compile(r"under\s*(\d+)\s*k\b", re.I)
RX_BUDGET_ANY  = re.compile(r"(?:under|below|less than|<=)\s*([0-9][0-9,]*)", re.I)

RX_RAM_GB      = _rx_num("gb")
RX_STORAGE_GB  = _rx_num("gb")
RX_STORAGE_TB  = _rx_num("tb")
RX_BATTERY_MAH = re.compile(r"\b(\d{3,5})\s*mAh\b", re.I)
RX_CAP_L       = _rx_num("l")
RX_SIZE_UK     = re.compile(r"\buk\s*(\d{1,2})\b", re.I)
RX_SIZE_US     = re.compile(r"\bus\s*(\d{1,2})\b", re.I)
RX_SIZE_EU     = re.compile(r"\beu\s*(\d{1,2})\b", re.I)

def _first_match(rx: re.Pattern, text: str) -> str | None:
    m = rx.search(text)
    return m.group(1) if m else None

def _contains_any(text: str, words: List[str]) -> List[str]:
    hits = []
    for w in words:
        if w in text:
            hits.append(w)
    return hits


# -----------------------------
# Main parser
# -----------------------------
def parse_constraints(query: str) -> Dict[str, Any]:
    """
    Category-agnostic parsing of NL query → constraints:
      - budget (INR)
      - category (electronics / fashion / home-kitchen / appliances / sports / beauty / None)
      - brand hints
      - color, material, size (UK/US/EU), capacity (L)
      - electronics hints: RAM (GB), storage (GB/TB), battery (mAh)
      - keywords: bag of useful tokens for generic ranking boost
    """
    q = query.lower()

    # --- budget ---
    budget = None
    m = RX_UNDER_K.search(q)
    if m:
        budget = int(float(m.group(1)) * 1000)
    else:
        n = RX_BUDGET_ANY.search(q)
        if n:
            budget = int(n.group(1).replace(",", ""))

    # --- category inference (take the first category that matches) ---
    category = None
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in q for k in kws):
            category = cat
            break

    # --- brand, color, material ---
    brands = _contains_any(q, BRANDS)
    colors = _contains_any(q, COLORS)
    materials = _contains_any(q, MATERIALS)

    # --- sizes / capacity (for shoes, bottles, cookware, etc.) ---
    size_uk = _first_match(RX_SIZE_UK, q)
    size_us = _first_match(RX_SIZE_US, q)
    size_eu = _first_match(RX_SIZE_EU, q)
    capacity_l = _first_match(RX_CAP_L, q)

    # --- electronics specifics (but kept optional for any category) ---
    ram_gb = _first_match(RX_RAM_GB, q) if "gb" in q else None
    storage_tb = _first_match(RX_STORAGE_TB, q) if "tb" in q else None
    storage_gb = _first_match(RX_STORAGE_GB, q) if ("gb" in q and not ram_gb) else None
    battery_mah = _first_match(RX_BATTERY_MAH, q)

    # --- free keywords for scoring (loose bag-of-words) ---
    keyword_bag: List[str] = []
    keyword_bag.extend(brands)
    keyword_bag.extend(colors)
    keyword_bag.extend(materials)
    for token in ["gaming","lightweight","waterproof","nonstick","non-stick","induction",
                  "wireless","bluetooth","noise cancelling","anc","fast charging",
                  "camera","5g","4g","dual sim","backlit","fingerprint"]:
        if token in q:
            keyword_bag.append(token)

    # --- filters dict (generic; category-agnostic) ---
    filters: Dict[str, Any] = {}
    if brands:       filters["brand"] = list(dict.fromkeys(brands))
    if colors:       filters["color"] = list(dict.fromkeys(colors))
    if materials:    filters["material"] = list(dict.fromkeys(materials))
    if size_uk:      filters["size_uk"] = size_uk
    if size_us:      filters["size_us"] = size_us
    if size_eu:      filters["size_eu"] = size_eu
    if capacity_l:   filters["capacity_l"] = capacity_l
    if ram_gb:       filters["ram_gb"] = ram_gb
    if storage_tb:   filters["storage_tb"] = storage_tb
    if storage_gb:   filters["storage_gb"] = storage_gb
    if battery_mah:  filters["battery_mah"] = battery_mah

    return {
        "budget": budget,          # int | None
        "category": category,      # str | None
        "filters": filters,        # Dict[str, Any]
        "keywords": keyword_bag,   # List[str]
    }
