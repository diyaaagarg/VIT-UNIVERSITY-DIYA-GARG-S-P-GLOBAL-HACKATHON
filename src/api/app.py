"""FastAPI service for persisted Phase 2 signals."""
from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.engine.models import Signal
from src.engine.persistence import load_signals
from src.utils.config import ROOT, settings

app = FastAPI(title="Unified AI/NLP Risk Engine", version="0.2.0")


def records(ticker: str | None = None, high_impact: float | None = None) -> list[Signal]:
    return load_signals(ROOT / settings().database_path, ticker, high_impact)


@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok", "mode": settings().mode}


@app.get("/signals", response_model=list[Signal])
def signals(limit: int = Query(default=100, ge=1, le=1000)) -> list[Signal]: return records()[:limit]


@app.get("/signals/{ticker}", response_model=list[Signal])
def ticker_signals(ticker: str) -> list[Signal]:
    result = records(ticker=ticker)
    if not result: raise HTTPException(status_code=404, detail=f"No signals for {ticker.upper()}")
    return result


@app.get("/events/high-impact", response_model=list[Signal])
def high_impact(minimum_impact: float = Query(default=7, ge=1, le=10)) -> list[Signal]: return records(high_impact=minimum_impact)


@app.get("/stream")
async def stream() -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        for signal in records()[:50]:
            yield f"event: signal\ndata: {signal.model_dump_json()}\n\n"
            await asyncio.sleep(0)
    return StreamingResponse(events(), media_type="text/event-stream")
