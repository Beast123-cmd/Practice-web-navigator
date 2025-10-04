from __future__ import annotations
from typing import Any, Dict, List

from ..schemas import Product
from ..agents.parser_agent import parse_constraints
from ..agents.navigator_agent import run as navigator_run
from ..agents.extractor_agent import run as extractor_run
from ..agents.ranker_agent import run as ranker_run
from ..agents.summarizer_agent import run as summarizer_run


async def parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  { query, constraints? }
    Output: adds/updates { constraints }
    """
    constraints = state.get("constraints") or parse_constraints(state["query"])
    return {**state, "constraints": constraints}


async def navigator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  { query, sites? }
    Output: adds { raw_results: List[Product] }
    """
    sites: List[str] = state.get("sites") or ["amazon", "flipkart"]
    raw: List[Product] = await navigator_run(state["query"], sites)
    return {**state, "raw_results": raw}


async def extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  { raw_results }
    Output: normalizes { raw_results } (kept thin for now)
    """
    products = await extractor_run(state.get("raw_results", []))
    return {**state, "raw_results": products}


async def ranker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  { query, constraints, raw_results, k? }
    Output: adds { ranked: List[Product] }
    """
    k = int(state.get("k", 6))
    ranked = await ranker_run(
        state.get("raw_results", []),
        state.get("constraints", {}),
        state["query"],
        k,
    )
    return {**state, "ranked": ranked}


async def summarizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:  { ranked, constraints, query }
    Output: adds { summary: str }
    """
    summary = await summarizer_run(
        state.get("ranked", []),
        state.get("constraints", {}),
        state["query"],
    )
    return {**state, "summary": summary}
