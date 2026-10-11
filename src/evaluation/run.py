"""Generate Phase 3 evaluation artifacts without requiring a network."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from src.engine.models import ProcessedDocument
from src.nlp.events import EventClassifier
from src.nlp.sentiment import SentimentAnalyzer
from src.evaluation.metrics import classification_report
from src.utils.config import ROOT


def evaluate_seed() -> dict[str, object]:
    docs = {ProcessedDocument.model_validate_json(line).id: ProcessedDocument.model_validate_json(line) for line in (ROOT / "data/processed/processed.jsonl").read_text().splitlines()}
    labels = [json.loads(line) for line in (ROOT / "data/labeled/event_labels_seed.jsonl").read_text().splitlines()]
    sentiment, events = SentimentAnalyzer(), EventClassifier()
    sentiment_truth: list[str] = []; sentiment_prediction: list[str] = []
    event_truth: list[str] = []; event_prediction: list[str] = []
    for label in labels:
        doc = docs[label["document_id"]]
        sentiment_truth.append({"pos": "positive", "neg": "negative", "neu": "neutral"}[label["expected_sentiment"]])
        sentiment_prediction.append(sentiment.analyze(doc.clean_text).label)
        event_truth.append(label["event_type"]); event_prediction.append(events.classify(doc.clean_text).event_type)
    return {"dataset": "synthetic_seed_proxy", "disclosure": "This is a hand-labeled synthetic demo set, not Financial PhraseBank. Place a licensed public benchmark under data/raw to extend evaluation.", "sentiment": classification_report(sentiment_truth, sentiment_prediction), "event_classification": classification_report(event_truth, event_prediction)}


def evaluate_phrasebank_if_present() -> dict[str, object]:
    """Optional CSV adapter: columns `text` and `label` (positive/negative/neutral)."""
    path = ROOT / "data/raw/financial_phrasebank.csv"
    if not path.exists(): return {"status": "skipped", "reason": "Place Financial PhraseBank-compatible CSV at data/raw/financial_phrasebank.csv with text,label columns."}
    import csv
    with path.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
    truth = [row["label"].strip().lower() for row in rows if row.get("text") and row.get("label")]
    predicted = [SentimentAnalyzer().analyze(row["text"]).label for row in rows if row.get("text") and row.get("label")]
    return {"status": "complete", "dataset": path.name, "metrics": classification_report(truth, predicted)}


def correlation_check() -> dict[str, object]:
    """Optional network-backed diagnostic; never makes the report fail."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return {"status": "skipped", "reason": "Optional yfinance is not installed. Install it to enable this diagnostic."}
    try:
        # Replay timestamps are illustrative, so this check uses symbols only if data is available.
        history = yf.download("SPY", period="3mo", auto_adjust=True, progress=False)
        if history.empty: return {"status": "skipped", "reason": "yfinance returned no market data."}
        return {"status": "skipped", "reason": "Replay timestamps are synthetic and are not appropriate for a real return correlation. Use a dated live/cached corpus for this diagnostic.", "market_rows_available": int(len(history))}
    except Exception as error:
        return {"status": "skipped", "reason": f"Market data unavailable: {type(error).__name__}"}


def write_report(result: dict[str, object]) -> Path:
    reports = ROOT / "reports"; reports.mkdir(exist_ok=True)
    target = reports / "phase3_evaluation.json"; target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    sentiment = result["seed_evaluation"]["sentiment"]; events = result["seed_evaluation"]["event_classification"]
    (reports / "phase3_evaluation.md").write_text(f"# Phase 3 Evaluation\n\n- Sentiment seed accuracy: {sentiment['accuracy']}\n- Sentiment seed macro F1: {sentiment['macro_f1']}\n- Event seed accuracy: {events['accuracy']}\n- Event seed macro F1: {events['macro_f1']}\n\n## Data disclosure\n\n{result['seed_evaluation']['disclosure']}\n\n## Return correlation\n\n{result['return_correlation']}\n", encoding="utf-8")
    return target


def main() -> None:
    result = {"seed_evaluation": evaluate_seed(), "phrasebank_evaluation": evaluate_phrasebank_if_present(), "return_correlation": correlation_check()}
    path = write_report(result)
    print(f"evaluation_report={path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
