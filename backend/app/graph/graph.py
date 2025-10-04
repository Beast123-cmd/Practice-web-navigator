from __future__ import annotations
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END

from ..schemas import Product
from .nodes import (
    parser_node,
    navigator_node,
    extractor_node,
    ranker_node,
    summarizer_node,
)


class GraphState(TypedDict):
    query: str
    constraints: Dict[str, Any]
    sites: List[str]
    k: int
    raw_results: List[Product]
    ranked: List[Product]
    summary: str


def build_graph():
    """
    Construct the LangGraph pipeline:
    parser → navigator → extractor → ranker → summarizer → END
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("parser", parser_node)
    workflow.add_node("navigator", navigator_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("ranker", ranker_node)
    workflow.add_node("summarizer", summarizer_node)

    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "navigator")
    workflow.add_edge("navigator", "extractor")
    workflow.add_edge("extractor", "ranker")
    workflow.add_edge("ranker", "summarizer")
    workflow.add_edge("summarizer", END)

    return workflow.compile()


# Create a module-level compiled graph for convenience/imports
compiled_graph = build_graph()

__all__ = ["GraphState", "build_graph", "compiled_graph"]
