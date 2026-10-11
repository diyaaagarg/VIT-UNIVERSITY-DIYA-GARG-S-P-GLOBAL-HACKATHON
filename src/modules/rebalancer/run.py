"""Create dashboard-ready rebalancer artifacts from Phase 2 signals."""
from __future__ import annotations
import json
from pathlib import Path
from src.engine.persistence import load_signals
from src.modules.rebalancer.backtest import performance, synthetic_returns
from src.modules.rebalancer.core import aggregate_sentiment, constrained_weights
from src.utils.config import ROOT, read_yaml, settings, universe


def main() -> None:
    cfg = read_yaml(ROOT / "config/rebalancer.yaml"); tickers = list(universe()["tickers"]); base = {ticker: 1 / len(tickers) for ticker in tickers}
    signals = load_signals(ROOT / settings().database_path)
    reference = max(signal.published_at for signal in signals)
    sentiment = aggregate_sentiment(signals, reference, cfg["half_life_hours"], cfg["min_confidence"])
    weights, turnover = constrained_weights(base, sentiment, cfg["tilt_k"], cfg["min_weight"], cfg["max_weight"], cfg["max_turnover"])
    triggers = [{"ticker": ticker, "weight_change": round(weights[ticker] - base[ticker], 4), "signals": [signal.id for signal in signals if signal.entity == ticker][:5]} for ticker in tickers if abs(weights[ticker] - base[ticker]) > 0.0001]
    result = {"as_of": reference.isoformat(), "base_weights": base, "target_weights": weights, "smoothed_sentiment": sentiment, "turnover": turnover, "constraints": {key: cfg[key] for key in ("min_weight", "max_weight", "max_turnover", "min_confidence")}, "triggers": triggers, "backtest": performance(synthetic_returns(tickers, cfg["backtest_days"], cfg["seed"]), base, weights), "price_data_disclosure": "Seeded synthetic daily returns are used for offline reproducibility; replace with licensed cached historical prices for production."}
    output = ROOT / "reports/rebalancer_result.json"; output.parent.mkdir(exist_ok=True); output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"rebalancer_report={output}")
    print(f"turnover={turnover:.4f} tactical_return={result['backtest']['tactical_return']:.2%} equal_weight_return={result['backtest']['equal_weight_return']:.2%}")


if __name__ == "__main__": main()
