"""Constraint-aware tactical sentiment rebalancer."""
from __future__ import annotations
import math
from datetime import datetime
from typing import Iterable
from src.engine.models import Signal


def aggregate_sentiment(signals: Iterable[Signal], reference_time: datetime, half_life_hours: float, min_confidence: float) -> dict[str, float]:
    """Confidence and time-weighted sentiment by linked ticker."""
    numerator: dict[str, float] = {}; denominator: dict[str, float] = {}
    for signal in signals:
        if signal.entity == "MARKET" or signal.confidence < min_confidence: continue
        age = max(0, (reference_time - signal.published_at).total_seconds() / 3600)
        weight = signal.confidence * math.exp(-math.log(2) * age / half_life_hours)
        numerator[signal.entity] = numerator.get(signal.entity, 0) + signal.sentiment_score * weight
        denominator[signal.entity] = denominator.get(signal.entity, 0) + weight
    return {ticker: numerator[ticker] / denominator[ticker] for ticker in numerator}


def _normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    return {key: value / total for key, value in values.items()} if total else values


def constrained_weights(base: dict[str, float], sentiment: dict[str, float], tilt_k: float, minimum: float, maximum: float, max_turnover: float) -> tuple[dict[str, float], float]:
    """Tilt, cap/floor, normalize, then scale the active tilt to a turnover limit."""
    raw = {ticker: base[ticker] * (1 + tilt_k * sentiment.get(ticker, 0)) for ticker in base}
    weights = _normalize(raw)
    for _ in range(10):
        weights = {ticker: min(maximum, max(minimum, value)) for ticker, value in weights.items()}
        weights = _normalize(weights)
    turnover = sum(abs(weights[ticker] - base[ticker]) for ticker in base) / 2
    if turnover > max_turnover:
        scale = max_turnover / turnover
        weights = {ticker: base[ticker] + scale * (weights[ticker] - base[ticker]) for ticker in base}
        turnover = max_turnover
    return weights, round(turnover, 6)
