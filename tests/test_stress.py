from src.modules.stress.engine import position_pnl, run_stress, scaled_shocks


POSITION = {"position_id": "x", "asset_class": "bond", "issuer": "x", "sector": "Financials", "region": "North America", "currency": "USD", "notional_usd": 1_000_000, "market_value_usd": 1_000_000, "rating": "A", "tenor_years": 5, "pd": .01, "lgd": .4, "duration": 5, "convexity": 10, "coupon": .04, "beta": 1, "delta": .5, "dv01": 1000}


def test_bond_rate_shock_and_severity_scaling() -> None:
    small, large = scaled_shocks("Macroeconomic", 3), scaled_shocks("Macroeconomic", 9)
    assert large["rate_bps"] > small["rate_bps"]
    assert position_pnl(POSITION, large) < 0


def test_stress_result_has_waterfall_components() -> None:
    result = run_stress([POSITION], "Credit Event", 8)
    assert result["post_value_usd"] < result["pre_value_usd"]
    assert len(result["top_affected_positions"]) == 1
