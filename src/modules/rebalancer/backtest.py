"""Small deterministic backtest used when no external price history is cached."""
from __future__ import annotations
import random
from typing import Iterable


def synthetic_returns(tickers: list[str], days: int, seed: int) -> list[dict[str, float]]:
    rng = random.Random(seed); rows = []
    for _ in range(days): rows.append({ticker: rng.gauss(0.00035, 0.014) for ticker in tickers})
    return rows


def performance(returns: Iterable[dict[str, float]], base: dict[str, float], tactical: dict[str, float]) -> dict[str, float | list[dict[str, float]]]:
    base_value = tactical_value = 1.0; history = []
    daily_base: list[float] = []; daily_tactical: list[float] = []
    for day, row in enumerate(returns):
        rb = sum(base[ticker] * row[ticker] for ticker in base); rt = sum(tactical[ticker] * row[ticker] for ticker in tactical)
        base_value *= 1 + rb; tactical_value *= 1 + rt; daily_base.append(rb); daily_tactical.append(rt)
        history.append({"day": day + 1, "equal_weight": round(base_value, 6), "tactical": round(tactical_value, 6)})
    def stats(values: list[float], ending: float) -> tuple[float, float]:
        mean = sum(values) / len(values); variance = sum((x - mean) ** 2 for x in values) / len(values)
        return (variance ** 0.5) * (252 ** 0.5), (mean / (variance ** 0.5) * (252 ** 0.5)) if variance else 0
    def drawdown(series: list[dict[str, float]], key: str) -> float:
        peak = 1.0; worst = 0.0
        for point in series: peak = max(peak, point[key]); worst = min(worst, point[key] / peak - 1)
        return worst
    bv, bs = stats(daily_base, base_value); tv, ts = stats(daily_tactical, tactical_value)
    return {"equal_weight_return": round(base_value - 1, 4), "tactical_return": round(tactical_value - 1, 4), "equal_weight_volatility": round(bv, 4), "tactical_volatility": round(tv, 4), "equal_weight_sharpe": round(bs, 3), "tactical_sharpe": round(ts, 3), "equal_weight_max_drawdown": round(drawdown(history, "equal_weight"), 4), "tactical_max_drawdown": round(drawdown(history, "tactical"), 4), "history": history}
