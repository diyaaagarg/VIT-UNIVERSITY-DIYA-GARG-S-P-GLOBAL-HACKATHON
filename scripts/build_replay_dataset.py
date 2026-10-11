"""Build deterministic, clearly synthetic replay data; network is optional."""
from __future__ import annotations
import json
import sys
import csv
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.models import RawDocument, SourceType
from src.ingestion.sources import RssSource
from src.utils.config import ROOT

START = datetime(2026, 1, 15, 13, 30, tzinfo=timezone.utc)
UNIVERSE = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "JPM", "BAC", "GS", "XOM", "CVX", "JNJ", "PFE", "WMT"]
NAMES = {"AAPL":"Apple", "MSFT":"Microsoft", "AMZN":"Amazon", "GOOGL":"Google", "META":"Meta Platforms", "NVDA":"NVIDIA", "TSLA":"Tesla", "JPM":"JPMorgan", "BAC":"Bank of America", "GS":"Goldman Sachs", "XOM":"ExxonMobil", "CVX":"Chevron", "JNJ":"Johnson & Johnson", "PFE":"Pfizer", "WMT":"Walmart"}


def synthetic(index: int, title: str, text: str, tickers: list[str], source_type: SourceType = SourceType.NEWS) -> RawDocument:
    return RawDocument(id=str(uuid5(NAMESPACE_URL, f"crisis-scenario-{index}")), source="synthetic_demo_news" if source_type == SourceType.NEWS else "synthetic_demo_social", source_type=source_type, title=title, text=text, published_at=START + timedelta(minutes=index * 5), tickers=tickers, raw_metadata={"scenario": "fictional_training_demo"}, is_synthetic=True)


def build_scenario() -> list[tuple[RawDocument, str, str]]:
    docs: list[tuple[RawDocument, str, str]] = []
    templates = [
        ("Earnings", "pos", "Synthetic market note: {name} reports routine quarterly demand in line with fictional analyst expectations."),
        ("Product Launch", "pos", "Synthetic product update: {name} previews a planned platform feature for demonstration purposes."),
        ("Other", "neu", "Synthetic trading note: observers discuss ordinary volume in {name} shares."),
    ]
    for i, ticker in enumerate(UNIVERSE):
        event, sentiment, text = templates[i % len(templates)]
        docs.append((synthetic(i, f"Synthetic: {NAMES[ticker]} routine market update", text.format(name=NAMES[ticker]), [ticker]), event, sentiment))
    specials = [
        ("Synthetic inflation release holds near expectations", "Fictional macro bulletin: inflation data and bond yields are steady in this simulated feed.", [], "Macroeconomic", "neu"),
        ("Synthetic regulator reviews platform disclosures", "Fictional regulatory review mentions Meta Platforms and disclosure controls.", ["META"], "Regulatory", "neu"),
        ("Synthetic cyber outage affects a fictional supplier", "Fictional cyber incident causes limited operational delays; no customer data is described.", [], "Cybersecurity/Operational", "neg"),
        ("Synthetic merger talks reported", "Fictional market chatter says a small supplier may seek a merger; this is not real reporting.", [], "Merger/Acquisition", "neu"),
        ("Synthetic credit watch for a fictional industrial borrower", "Fictional credit event: a non-universe borrower faces a ratings review and wider credit spreads.", [], "Credit Event", "neg"),
    ]
    for offset, (title, text, tickers, event, sentiment) in enumerate(specials, start=15):
        docs.append((synthetic(offset, title, text, tickers), event, sentiment))
    buildup = [
        ("Synthetic shipping alert raises Strait of Hormuz concern", "Fictional geopolitical scenario: reports of shipping delays near the Strait of Hormuz lift oil-risk discussion.", ["XOM", "CVX"], "Geopolitical", "neg"),
        ("Synthetic social post: watching $XOM and $CVX", "Demo social chatter: shipping tension could affect oil and energy stocks; this post is synthetic.", ["XOM", "CVX"], "Geopolitical", "neg"),
        ("Synthetic energy desk notes rising crude volatility", "Fictional analyst note: oil and refinery markets price higher volatility amid Hormuz uncertainty.", ["XOM", "CVX"], "Geopolitical", "neg"),
        ("Synthetic breaking alert: Hormuz transit interruption", "Fictional breaking-news simulation: a Strait of Hormuz transit interruption triggers an oil shock and broad risk-off move.", ["XOM", "CVX", "JPM", "BAC"], "Geopolitical", "neg"),
        ("Synthetic social reaction to the Hormuz event", "Demo social chatter lags the news: $XOM $CVX oil shock and bank-risk discussion in a simulated feed.", ["XOM", "CVX", "JPM", "BAC"], "Geopolitical", "neg"),
        ("Synthetic consumer and travel demand warning", "Fictional follow-up: higher fuel costs could pressure consumer demand and airline-linked spending.", ["AMZN", "WMT", "TSLA"], "Geopolitical", "neg"),
        ("Synthetic banks assess market volatility", "Fictional follow-up: JPMorgan, Bank of America and Goldman Sachs monitor market liquidity and credit spreads.", ["JPM", "BAC", "GS"], "Credit Event", "neg"),
    ]
    for offset, (title, text, tickers, event, sentiment) in enumerate(buildup, start=20):
        docs.append((synthetic(offset, title, text, tickers), event, sentiment))
    # Deliberate exact and near duplicates, non-English and irrelevant samples.
    docs.append((synthetic(27, "Synthetic breaking alert: Hormuz transit interruption", "Fictional breaking-news simulation: a Strait of Hormuz transit interruption triggers an oil shock and broad risk-off move.", ["XOM", "CVX", "JPM", "BAC"]), "Geopolitical", "neg"))
    docs.append((synthetic(28, "Synthetic Hormuz transit interruption update", "Fictional breaking news simulation: Strait of Hormuz transit interruption triggers oil shock and broad risk off move.", ["XOM", "CVX"]), "Geopolitical", "neg"))
    docs.append((synthetic(29, "Actualización sintética sobre mercados", "Boletín ficticio: los mercados siguen la inflación y el petróleo.", []), "Macroeconomic", "neu"))
    docs.append((synthetic(30, "Synthetic local weather bulletin", "Fictional community notice: mild weather is expected this weekend; unrelated to financial markets.", []), "Other", "neu"))
    while len(docs) < 70:
        i = len(docs); ticker = UNIVERSE[i % len(UNIVERSE)]; event, sentiment, text = templates[i % len(templates)]
        source_type = SourceType.SOCIAL if i % 3 == 0 else SourceType.NEWS
        docs.append((synthetic(i, f"Synthetic follow-up: {NAMES[ticker]} market discussion", text.format(name=NAMES[ticker]), [ticker], source_type), event, sentiment))
    return docs


def main() -> None:
    replay = ROOT / "data/replay"; labeled = ROOT / "data/labeled"; replay.mkdir(parents=True, exist_ok=True); labeled.mkdir(parents=True, exist_ok=True)
    # These caches are deliberately separate from the deterministic crisis demo.
    # A failed network request simply leaves the offline scenario untouched.
    try:
        logging.getLogger("src.ingestion.sources").setLevel(logging.ERROR)
        recent = asyncio.run(RssSource().fetch())
        if recent:
            (replay / "news_cached.jsonl").write_text("".join(item.model_dump_json() + "\n" for item in recent), encoding="utf-8")
            print(f"cached {len(recent)} live RSS records to data/replay/news_cached.jsonl")
        else:
            print("live RSS cache unavailable; retained deterministic offline replay")
    except Exception as error:
        print(f"live RSS cache skipped safely: {error}")
    tweets_csv = ROOT / "data/raw/financial_tweets.csv"
    if tweets_csv.exists():
        social: list[RawDocument] = []
        with tweets_csv.open(encoding="utf-8", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                text = row.get("text") or row.get("tweet") or row.get("content")
                if not text: continue
                stamp = row.get("timestamp") or row.get("date") or START.isoformat()
                try: published = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                except ValueError: published = START + timedelta(minutes=index)
                social.append(RawDocument(source="local_financial_tweets", source_type=SourceType.SOCIAL, text=text, author=row.get("author") or row.get("user"), published_at=published, raw_metadata={"dataset": tweets_csv.name}, is_synthetic=False))
        (replay / "social_cached.jsonl").write_text("".join(item.model_dump_json() + "\n" for item in social), encoding="utf-8")
        print(f"converted {len(social)} local social records to data/replay/social_cached.jsonl")
    scenario = build_scenario()
    with (replay / "crisis_scenario.jsonl").open("w", encoding="utf-8") as handle:
        for doc, _, _ in scenario: handle.write(doc.model_dump_json() + "\n")
    with (labeled / "event_labels_seed.jsonl").open("w", encoding="utf-8") as handle:
        for doc, event_type, sentiment in scenario[:50]: handle.write(json.dumps({"document_id": doc.id, "event_type": event_type, "expected_sentiment": sentiment, "expected_tickers": doc.tickers, "is_synthetic": True}) + "\n")
    print("created data/replay/crisis_scenario.jsonl (70 synthetic documents)")
    print("created data/labeled/event_labels_seed.jsonl (50 labels)")
    print("Optional social cache: place a licensed Kaggle/public CSV at data/raw/financial_tweets.csv with text (or tweet/content), optional timestamp/date, and optional author/user columns.")

if __name__ == "__main__": main()
