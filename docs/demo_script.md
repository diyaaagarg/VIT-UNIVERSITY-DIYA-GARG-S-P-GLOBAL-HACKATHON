# Five-Minute Judge Demo

This demo is deterministic and uses clearly labeled synthetic replay data. Begin with `make demo`, then open the Streamlit URL shown in the terminal.

| Time | Say / show |
|---|---|
| 0:00–0:25 | “This is an offline-first AI risk engine. It converts unstructured news and social text into sentiment, event, impact, and confidence signals.” Show the **Live Signal Feed** tab and its Replay/Live selector. |
| 0:25–1:05 | Point out the synthetic marker and select a Strait of Hormuz signal. Explain the visible geopolitical event type, negative sentiment, high impact, source confidence, and explainable score factors. |
| 1:05–1:40 | Open **Index Rebalancer**. Contrast equal-weight with tactical allocation, show turnover is constrained, then point to the trigger feed that links allocation moves to source signals. |
| 1:40–2:25 | Show the backtest disclosure: it is seeded offline data for reproducibility, not a live investment claim. Point out cumulative return, volatility, Sharpe, and maximum drawdown fields. |
| 2:25–3:15 | Open **Stress Test**. Show the $1B, 150-position synthetic wholesale portfolio, latest portfolio P&L, sector breakdown, and worst affected positions. |
| 3:15–4:20 | In **Simulate breaking news**, keep the default Hormuz headline and click **Run end-to-end simulation**. Narrate: headline → entity links to XOM/CVX → geopolitical/negative signal → impact 7.84 → automatic stress run. |
| 4:20–4:45 | Open **Model Evaluation**. State the seed-set metrics honestly and point out the synthetic-proxy disclosure and Financial PhraseBank adapter. |
| 4:45–5:00 | Open **Architecture / About**. Close with: “The key is robust actionability: reproducible replay when live feeds fail, explainable signals, and two downstream risk decisions.” |

## Recovery path

If any external feed is unavailable, keep Replay selected. Everything needed for the demo is local. Run `make analyze-demo`, `make rebalance-demo`, `make stress-demo`, and `make evaluate` to regenerate individual artifacts.
