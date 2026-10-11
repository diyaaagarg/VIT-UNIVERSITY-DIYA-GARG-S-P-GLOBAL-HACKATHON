# Likely Judge Questions and Answers

**Why should we trust a score derived from text?**  We do not treat it as a trading decision by itself. Each score is decomposed into explicit severity, sentiment, source-credibility, recency, and volume factors, then passed through configurable guardrails.

**What happens if live data fails during a demo or production?**  The source manager logs the issue and switches to replay. In production, the same behavior becomes an alert plus last-known-good/cache policy rather than a silent failure.

**Is the training/evaluation data real?**  The replay scenario and initial labels are explicitly synthetic. The system includes a Financial PhraseBank-compatible adapter and reports its data disclosure in the UI. Production evaluation requires licensed data and governance approval.

**Why not use an LLM for everything?**  The default is local, deterministic, CPU-safe logic for reproducibility and explainability. The contracts isolate NLP components so a governed model can be substituted later.

**How do you avoid false entity links?**  Match order prioritizes cashtags/tickers, then bounded aliases, then optional spaCy ORG matching. Ambiguous words such as Apple and Amazon require financial context; macro-only text becomes MARKET.

**How are portfolio valuations defensible?**  The demo intentionally uses documented first-order approximations: duration/convexity for bonds, PD×LGD×EAD for loans, and delta/DV01 for derivatives. They are transparent and replaceable with desk-approved pricing models.

**Can this connect to our transaction data?**  Yes. `config/portfolio.yaml` holds a column map, and `data/raw/transactions.csv` is loaded through the adapter. The synthetic portfolio is only a reproducible fallback.

**Why is the backtest synthetic?**  Reliable offline judging was prioritized. The result is disclosed as seeded synthetic data and should not be construed as investment performance. The data interface can accept licensed cached historical prices.

**What controls rebalancing risk?**  Minimum confidence, floors, caps, and maximum turnover are configuration-backed and visible in the dashboard.

**What would a pilot require?**  Approved data access, source licensing, historical labeled data, model-risk review, monitoring thresholds, and a human approval workflow before portfolio action.
