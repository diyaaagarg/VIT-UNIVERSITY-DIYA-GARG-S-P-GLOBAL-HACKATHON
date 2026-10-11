"""Convert stable Phase 1 documents into Phase 2 risk signals."""
from __future__ import annotations
from src.engine.models import ProcessedDocument, Signal
from src.engine.scoring import impact_score
from src.nlp.events import EventClassifier
from src.nlp.sentiment import SentimentAnalyzer

SOURCE_CREDIBILITY = {"news": 0.8, "social": 0.5}


class RiskEngine:
    def __init__(self) -> None:
        self.sentiment = SentimentAnalyzer(); self.events = EventClassifier()

    def analyze(self, document: ProcessedDocument) -> list[Signal]:
        sentiment = self.sentiment.analyze(document.clean_text)
        event = self.events.classify(document.clean_text)
        tickers = [entity.ticker for entity in document.entities]
        entities = tickers or ["MARKET"]
        credibility = SOURCE_CREDIBILITY[document.source_type.value]
        score, explanation = impact_score(event.event_type, sentiment.score, credibility, document.published_at, document.duplicate_count, replay_mode=document.is_synthetic)
        confidence = round(min(0.98, (sentiment.confidence + event.confidence) / 2), 2)
        return [Signal(document_id=document.id, source=document.source, source_type=document.source_type, entity=entity, tickers=tickers, text=document.clean_text, published_at=document.published_at, sentiment_score=sentiment.score, sentiment_label=sentiment.label, event_type=event.event_type, impact_score=score, confidence=confidence, explanation=explanation, is_synthetic=document.is_synthetic) for entity in entities]
