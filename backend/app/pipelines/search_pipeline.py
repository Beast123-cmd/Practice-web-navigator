from __future__ import annotations
from typing import Any, Dict, List, Optional
from ..graph.graph import compiled_graph


async def run_pipeline(
    query: str,
    max_price: Optional[int],
    sites: List[str],
    k: int,
    category_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orchestrates the 5-agent LangGraph pipeline end-to-end.

    Inputs:
      - query: natural language from the chatbot (any product type)
      - max_price: optional INR budget (e.g., 50000)
      - sites: marketplaces to search (e.g., ["amazon","flipkart"])
      - k: number of top results to return
      - category_hint: optional hint from UI (parser will still infer category)

    Returns:
      - final state dict with keys:
        { query, constraints, sites, k, raw_results, ranked, summary }
    """
    # Seed the shared graph state. Parser will enhance constraints (category, filters, keywords).
    constraints: Dict[str, Any] = {"budget": max_price, "keywords": []}
    if category_hint:
        constraints["category"] = category_hint

    init_state = {
        "query": query,
        "constraints": constraints,
        "sites": sites,
        "k": k,
        "raw_results": [],
        "ranked": [],
        "summary": "",
    }

    # Run the compiled graph (parser → navigator → extractor → ranker → summarizer)
    state = await compiled_graph.ainvoke(init_state)
    return state
