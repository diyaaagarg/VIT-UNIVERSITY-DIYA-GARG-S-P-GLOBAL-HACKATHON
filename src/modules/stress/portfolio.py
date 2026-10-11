"""Reproducible wholesale-bank portfolio generator and configurable loader."""
from __future__ import annotations
import json
import random
import csv
from pathlib import Path
from src.utils.config import ROOT, read_yaml

SECTORS = ["Technology", "Financials", "Energy", "Health Care", "Consumer"]
REGIONS = ["North America", "Europe", "Asia Pacific", "Emerging Markets"]
RATINGS = ["AAA", "AA", "A", "BBB", "BB"]


def generate_portfolio() -> list[dict]:
    cfg = read_yaml(ROOT / "config/portfolio.yaml"); rng = random.Random(cfg["seed"]); count = cfg["position_count"]; total = cfg["total_notional_usd"]
    mixes = [("loan", cfg["allocation"]["loan"]), ("bond", cfg["allocation"]["bond"]), ("derivative", cfg["allocation"]["derivative"]), ("equity_fx", cfg["allocation"]["equity_fx"])]
    positions: list[dict] = []; index = 0
    for asset_class, allocation in mixes:
        amount = total * allocation; n = round(count * allocation); each = amount / n
        for _ in range(n):
            index += 1; sector = rng.choice(SECTORS); region = rng.choice(REGIONS); rating = rng.choice(RATINGS)
            position = {"position_id": f"POS-{index:03d}", "asset_class": asset_class, "issuer": f"Synthetic {sector} Counterparty {index}", "sector": sector, "region": region, "currency": "USD", "notional_usd": round(each, 2), "market_value_usd": round(each, 2), "rating": rating, "tenor_years": rng.randint(1, 10), "pd": {"AAA": .002, "AA": .004, "A": .008, "BBB": .02, "BB": .06}[rating], "lgd": rng.uniform(.35, .55), "duration": rng.uniform(1, 8), "convexity": rng.uniform(2, 20), "coupon": rng.uniform(.02, .07), "beta": rng.uniform(.6, 1.4), "delta": rng.choice([-1, 1]) * rng.uniform(.3, .8), "dv01": rng.uniform(200, 2000)}
            positions.append(position)
    return positions


def load_or_create() -> list[dict]:
    transaction_file = ROOT / "data/raw/transactions.csv"
    if transaction_file.exists():
        return load_transaction_csv(transaction_file)
    path = ROOT / "data/portfolio/synthetic_portfolio.json"; path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): return json.loads(path.read_text())
    portfolio = generate_portfolio(); path.write_text(json.dumps(portfolio, indent=2)); return portfolio


def load_transaction_csv(path: Path) -> list[dict]:
    """Config-mapped adapter for a future supplied transaction file."""
    mapping = read_yaml(ROOT / "config/portfolio.yaml")["column_mapping"]
    defaults = {"issuer": "Imported Counterparty", "currency": "USD", "rating": "BBB", "tenor_years": 5, "pd": .02, "lgd": .45, "duration": 5.0, "convexity": 10.0, "coupon": .04, "beta": 1.0, "delta": .5, "dv01": 1000.0}
    output = []
    with path.open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle), start=1):
            position = {field: row.get(column) for field, column in mapping.items()}
            position.update({key: row.get(key, value) or value for key, value in defaults.items()})
            position["position_id"] = position.get("position_id") or f"IMPORTED-{index:03d}"
            position["market_value_usd"] = float(row.get("market_value_usd") or position["notional_usd"])
            position["notional_usd"] = float(position["notional_usd"])
            for key in ("pd", "lgd", "duration", "convexity", "coupon", "beta", "delta", "dv01"): position[key] = float(position[key])
            output.append(position)
    return output
