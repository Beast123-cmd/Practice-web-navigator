from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    """Request from the frontend chatbot."""
    query: str
    max_price: Optional[int] = Field(default=None, description="Budget cap in INR (e.g., 50000)")
    sites: List[str] = Field(default_factory=lambda: ["amazon", "flipkart"])
    k: int = Field(default=6, ge=1, le=12)
    # Optional hint from UI or future filters (not required)
    category_hint: Optional[str] = None     # e.g., "shoes", "mobiles", "utensils"

class Product(BaseModel):
    """Internal normalized product used inside the pipeline."""
    title: str
    price: Optional[float] = None           # numeric INR
    currency: str = "INR"
    rating: Optional[float] = None          # 0..5
    review_count: Optional[int] = None
    url: str
    image: Optional[str] = None
    source: str                              # "amazon" | "flipkart" | ...
    # New: category + flexible attributes for any vertical
    category: Optional[str] = None           # e.g., electronics/shoes/home-kitchen
    attrs: Dict[str, Any] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)

class UIProduct(BaseModel):
    """UI-friendly model expected by your React pages."""
    name: str
    price: str                               # formatted: "₹45,000"
    rating: Optional[float] = None
    specifications: List[str] = Field(default_factory=list)  # short, human-readable attrs
    link: str
    image: Optional[str] = None
    source: str
    reviewCount: Optional[int] = None
    rawTitle: Optional[str] = None
    # Optional: surface category if you want to show chips/filters
    category: Optional[str] = None

class SearchResponse(BaseModel):
    """Backend response: internal + UI data."""
    top_k: List[Product]     # for dev/debug or advanced UI
    results: List[UIProduct] # your UI consumes this
    summary: str
    debug: Dict[str, Any] = Field(default_factory=dict)
