"""Scenario shock scaling and simplified but auditable valuations."""
from __future__ import annotations
from collections import defaultdict
from src.utils.config import ROOT, read_yaml


def scaled_shocks(event_type: str, impact_score: float) -> dict[str, float]:
    base = read_yaml(ROOT / "config/stress.yaml")["scenario_shocks"].get(event_type) or read_yaml(ROOT / "config/stress.yaml")["scenario_shocks"]["Other"]
    scale = max(0.2, min(1.5, impact_score / 7))
    return {key: round(value * scale, 6) for key, value in base.items()} | {"severity_scale": round(scale, 3)}


def position_pnl(position: dict, shocks: dict[str, float]) -> float:
    value = position["market_value_usd"]; kind = position["asset_class"]
    if kind == "loan": return -value * min(1, position["pd"] * shocks["pd_multiplier"] * min(1, position["lgd"] + shocks["lgd_uplift"]))
    if kind == "bond":
        rate = shocks["rate_bps"] / 10_000; spread = shocks["spread_bps"] / 10_000
        return value * (-position["duration"] * (rate + spread) + .5 * position["convexity"] * (rate + spread) ** 2)
    if kind == "derivative": return position["delta"] * value * shocks["equity"] - position["dv01"] * shocks["rate_bps"]
    shock = shocks["oil"] if position["sector"] == "Energy" else shocks["equity"]
    return value * position["beta"] * shock


def run_stress(positions: list[dict], event_type: str, impact_score: float, signal_id: str = "manual") -> dict:
    shocks = scaled_shocks(event_type, impact_score); results = []
    for position in positions:
        pnl = position_pnl(position, shocks); results.append({**position, "pnl_usd": round(pnl, 2), "post_value_usd": round(position["market_value_usd"] + pnl, 2)})
    def grouped(key: str) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for row in results: out[row[key]] += row["pnl_usd"]
        return {name: round(value, 2) for name, value in sorted(out.items())}
    pre = sum(row["market_value_usd"] for row in positions); pnl = sum(row["pnl_usd"] for row in results)
    return {"triggered_by_signal_id": signal_id, "event_type": event_type, "impact_score": impact_score, "shocks": shocks, "pre_value_usd": round(pre, 2), "post_value_usd": round(pre + pnl, 2), "pnl_usd": round(pnl, 2), "pnl_by_asset_class": grouped("asset_class"), "pnl_by_sector": grouped("sector"), "pnl_by_region": grouped("region"), "top_affected_positions": sorted(results, key=lambda row: row["pnl_usd"])[:10]}
