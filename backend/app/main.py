from __future__ import annotations
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import SearchRequest, SearchResponse, Product
from .adapters.ui_mapper import map_many
from .pipelines.search_pipeline import run_pipeline

app = FastAPI(title="Web Navigator AI", version="0.4.0")

# Loosen CORS for dev; restrict in prod (set your frontend origin).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # e.g., ["http://localhost:5173", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """
    Chatbot entrypoint:
      - Runs the 5-agent LangGraph pipeline (parser → navigator → extractor → ranker → summarizer)
      - Maps internal products to UI-friendly objects for your React pages
    """
    try:
        state: Dict[str, Any] = await run_pipeline(
            query=req.query,
            max_price=req.max_price,
            sites=req.sites,
            k=req.k,
            category_hint=req.category_hint,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")

    ranked: list[Product] = state.get("ranked", [])
    ui_results = map_many(ranked)

    return SearchResponse(
        top_k=ranked,                         # internal objects (debug/advanced UI)
        results=ui_results,                   # UI-friendly results (your React pages consume this)
        summary=state.get("summary", ""),
        debug={
            "constraints": state.get("constraints"),
            "raw_count": len(state.get("raw_results", [])),
            "sites": state.get("sites"),
        },
    )
