"""CPU-safe financial sentiment with an optional FinBERT extension point."""
from __future__ import annotations
import re
from dataclasses import dataclass

POSITIVE = {"beat", "beats", "growth", "gain", "gains", "strong", "upgrade", "surge", "rally", "positive", "record", "improve", "approval", "resilient", "profit", "demand", "feature", "preview", "routine"}
NEGATIVE = {"risk", "risks", "fall", "falls", "drop", "decline", "loss", "losses", "downgrade", "default", "breach", "outage", "sanctions", "blockade", "widen", "warning", "pressure", "disrupt", "shock", "tension", "uncertainty", "delay", "delays", "interruption", "volatility", "liquidity"}


@dataclass(frozen=True)
class SentimentResult:
    score: float
    label: str
    confidence: float
    backend: str = "lexicon"


class SentimentAnalyzer:
    """Uses a transparent fallback that never downloads models during a demo."""
    def analyze(self, text: str) -> SentimentResult:
        tokens = re.findall(r"[a-z']+", text.lower())
        pos, neg = sum(token in POSITIVE for token in tokens), sum(token in NEGATIVE for token in tokens)
        score = round((pos - neg) / max(pos + neg, 3), 3)
        if score > 0.1: label = "positive"
        elif score < -0.1: label = "negative"
        else: label = "neutral"
        confidence = round(min(0.9, 0.45 + 0.1 * (pos + neg)), 2)
        return SentimentResult(score, label, confidence)
