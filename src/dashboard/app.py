"""Demo-ready Streamlit cockpit for the unified risk engine."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.engine.persistence import load_signals
from src.modules.stress.simulate import simulate
from src.utils.config import ROOT, settings

st.set_page_config(page_title="Unified Risk Engine", page_icon="◈", layout="wide")


def load_json(relative: str, fallback: object) -> object:
    path = ROOT / relative
    return json.loads(path.read_text()) if path.exists() else fallback


@st.cache_data(ttl=5)
def signals_frame() -> pd.DataFrame:
    rows = [signal.model_dump(mode="json") for signal in load_signals(ROOT / settings().database_path)]
    return pd.DataFrame(rows)


def metric_card(label: str, value: str, detail: str = "") -> None:
    st.metric(label, value, detail or None)


with st.sidebar:
    st.title("Risk Engine")
    mode = st.radio("Data mode", ["Replay", "Live"], index=0, help="Live safely falls back to replay when feeds or credentials are unavailable.")
    speed = st.select_slider("Replay speed", options=["1x", "10x", "60x", "instant"], value="instant")
    st.caption("Offline-first demo · synthetic replay items are visibly labeled.")
    if st.button("Reload dashboard data", use_container_width=True):
        st.cache_data.clear(); st.rerun()

feed_tab, rebalancer_tab, stress_tab, evaluation_tab, about_tab = st.tabs(["Live Signal Feed", "Index Rebalancer", "Stress Test", "Model Evaluation", "Architecture / About"])

with feed_tab:
    st.header("Live Signal Feed")
    frame = signals_frame()
    if frame.empty:
        st.info("No signals yet. Run `make analyze-demo` to populate replay signals.")
    else:
        cols = st.columns(4)
        with cols[0]: metric_card("Signals", str(len(frame)))
        with cols[1]: metric_card("High impact", str((frame["impact_score"] >= 7).sum()))
        with cols[2]: metric_card("Avg. confidence", f"{frame['confidence'].mean():.0%}")
        with cols[3]: metric_card("Mode", mode + (f" · {speed}" if mode == "Replay" else ""))
        view = frame[["published_at", "entity", "sentiment_label", "sentiment_score", "event_type", "impact_score", "confidence", "source", "is_synthetic"]].copy()
        view["published_at"] = view["published_at"].str.replace("T", " ").str[:19]
        st.dataframe(view, use_container_width=True, hide_index=True, column_config={"is_synthetic": st.column_config.CheckboxColumn("Synthetic demo")})
        chart = px.scatter(frame, x="sentiment_score", y="impact_score", color="event_type", size="confidence", hover_data=["entity", "source"], title="Signal sentiment vs. impact")
        st.plotly_chart(chart, use_container_width=True)

with rebalancer_tab:
    st.header("Tactical Index Rebalancer")
    result = load_json("reports/rebalancer_result.json", {})
    if not result:
        st.info("Run `make rebalance-demo` to generate allocation and backtest data.")
    else:
        base, target = result["base_weights"], result["target_weights"]
        weights = pd.DataFrame({"Ticker": list(base), "Base weight": list(base.values()), "Target weight": [target[t] for t in base], "Change": [target[t] - base[t] for t in base]}).sort_values("Change")
        left, right = st.columns([1, 2])
        with left:
            metric_card("Turnover", f"{result['turnover']:.2%}", f"Cap {result['constraints']['max_turnover']:.0%}")
            st.dataframe(weights.style.format({"Base weight": "{:.2%}", "Target weight": "{:.2%}", "Change": "{:+.2%}"}), use_container_width=True, hide_index=True)
        with right:
            history = pd.DataFrame(result["backtest"]["history"])
            fig = go.Figure([go.Scatter(x=history.day, y=history.equal_weight, name="Equal weight"), go.Scatter(x=history.day, y=history.tactical, name="Tactical")])
            fig.update_layout(title="Backtest: cumulative portfolio value", yaxis_tickformat=".2f")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(result["price_data_disclosure"])
        st.subheader("Signals driving allocation changes")
        st.dataframe(pd.DataFrame(result["triggers"]), use_container_width=True, hide_index=True)

with stress_tab:
    st.header("Event-Driven Portfolio Stress Test")
    history = load_json("reports/stress_history.json", [])
    left, right = st.columns([1, 1])
    with left:
        headline = st.text_area("Simulate breaking news", "Breaking simulation: Strait of Hormuz transit interruption triggers oil shock and broad market risk.")
        if st.button("Run end-to-end simulation", type="primary"):
            st.session_state["simulation"] = simulate(headline)
        simulation = st.session_state.get("simulation")
        if simulation:
            signals = pd.DataFrame(simulation["signals"])
            st.success("Stress test auto-triggered" if simulation["auto_triggered"] else "Signal remained below the auto-trigger threshold")
            st.dataframe(signals[["entity", "event_type", "sentiment_score", "impact_score", "confidence"]], use_container_width=True, hide_index=True)
            if simulation["stress_runs"]:
                latest = simulation["stress_runs"][0]
                metric_card("Simulated portfolio P&L", f"${latest['pnl_usd']:,.0f}")
                st.plotly_chart(px.bar(x=list(latest["pnl_by_asset_class"].keys()), y=list(latest["pnl_by_asset_class"].values()), labels={"x": "Asset class", "y": "P&L (USD)"}, title="P&L by asset class"), use_container_width=True)
    with right:
        if history:
            latest = history[0]
            metric_card("Latest auto stress P&L", f"${latest['pnl_usd']:,.0f}")
            st.plotly_chart(px.bar(x=list(latest["pnl_by_sector"].keys()), y=list(latest["pnl_by_sector"].values()), title="Latest stress: P&L by sector", labels={"x": "Sector", "y": "P&L (USD)"}), use_container_width=True)
            st.dataframe(pd.DataFrame(latest["top_affected_positions"])[["position_id", "asset_class", "sector", "region", "pnl_usd"]], use_container_width=True, hide_index=True)
        else: st.info("Run `make stress-demo` to generate auto-trigger history.")

with evaluation_tab:
    st.header("Model Evaluation")
    evaluation = load_json("reports/phase3_evaluation.json", {})
    if evaluation:
        seed = evaluation["seed_evaluation"]
        one, two = st.columns(2)
        with one:
            metric_card("Sentiment accuracy", f"{seed['sentiment']['accuracy']:.1%}")
            metric_card("Sentiment macro F1", f"{seed['sentiment']['macro_f1']:.3f}")
        with two:
            metric_card("Event accuracy", f"{seed['event_classification']['accuracy']:.1%}")
            metric_card("Event macro F1", f"{seed['event_classification']['macro_f1']:.3f}")
        st.warning(seed["disclosure"])
        st.json(evaluation["return_correlation"])
    else: st.info("Run `make evaluate` to generate metrics.")

with about_tab:
    st.header("Architecture & Demo Notes")
    st.code("""RSS / optional APIs / social cache
       ↓  (live sources safely fall back to deterministic replay)
Preprocess → entity linking → local NLP → explainable impact scoring
       ↓                         ↓                    ↓
SQLite + JSONL + FastAPI/SSE    Index rebalancer      Auto stress testing
       └──────────────────────────── Streamlit dashboard ────────────────────────────┘""", language="text")
    st.markdown("**Demo narrative:** replay the crisis timeline, open a high-impact signal, show the changed index weights, then type a breaking headline and watch the portfolio stress test trigger.")
    st.caption("All replay articles and social posts are synthetic, clearly labeled demo data. Live providers are optional and must be verified for terms and limits.")
