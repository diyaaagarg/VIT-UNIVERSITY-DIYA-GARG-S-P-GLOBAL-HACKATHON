import json
from pathlib import Path
from src.nlp.entity_linking import EntityLinker
from src.nlp.preprocessing import clean_text
from src.utils.config import ROOT


def test_alias_cashtag_ambiguity_and_macro() -> None:
    linker = EntityLinker()
    entities, tags = linker.link("$AAPL shares rise while oil prices climb", ["AAPL"])
    assert entities[0].ticker == "AAPL" and entities[0].match_type == "cashtag"
    assert "oil_energy" in tags and {item.ticker for item in entities} >= {"XOM", "CVX"}
    entities, _ = linker.link("An apple fruit recipe from an orchard")
    assert not any(item.ticker == "AAPL" for item in entities)
    entities, tags = linker.link("A cyber breach disrupts regional systems")
    assert tags == ["cyber"] and entities[0].ticker == "MARKET"


def test_seed_linking_recall_precision() -> None:
    linker = EntityLinker(); scenario = {}
    for line in (ROOT / "data/replay/crisis_scenario.jsonl").read_text().splitlines():
        row = json.loads(line); scenario[row["id"]] = row
    labels = [json.loads(line) for line in (ROOT / "data/labeled/event_labels_seed.jsonl").read_text().splitlines()]
    expected = predicted = correct = 0
    for label in labels:
        row = scenario[label["document_id"]]; truth = set(label["expected_tickers"])
        links, _ = linker.link(f"{row['title']} {row['text']}", row["tickers"])
        got = {item.ticker for item in links if item.match_type != "macro_sector"}
        expected += len(truth); predicted += len(got); correct += len(truth & got)
    precision = correct / predicted if predicted else 1
    recall = correct / expected if expected else 1
    assert precision >= 0.90 and recall >= 0.90, (precision, recall)
