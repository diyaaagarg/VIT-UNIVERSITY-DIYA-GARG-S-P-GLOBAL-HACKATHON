"""Auto-trigger stress tests from high-impact Phase 2 signals."""
from __future__ import annotations
import json
from src.engine.persistence import load_signals
from src.modules.stress.engine import run_stress
from src.modules.stress.portfolio import load_or_create
from src.utils.config import ROOT, read_yaml, settings


def main() -> None:
    cfg = read_yaml(ROOT / "config/stress.yaml"); threshold = cfg["auto_trigger_impact"]
    signals = load_signals(ROOT / settings().database_path, high_impact=threshold); portfolio = load_or_create()
    history = [run_stress(portfolio, signal.event_type, signal.impact_score, signal.id) for signal in signals]
    output = ROOT / "reports/stress_history.json"; output.parent.mkdir(exist_ok=True); output.write_text(json.dumps(history, indent=2))
    print(f"portfolio_positions={len(portfolio)} auto_triggered_runs={len(history)}")
    if history: print(f"latest_pnl={history[0]['pnl_usd']:,.2f} latest_post_value={history[0]['post_value_usd']:,.2f}")


if __name__ == "__main__": main()
