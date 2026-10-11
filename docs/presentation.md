# Seven-Slide Presentation Content

## 1. Unified AI/NLP Risk Engine

- From unstructured financial text to actionable risk decisions.
- Two downstream modules: tactical index rebalancing and wholesale-portfolio stress testing.
- Built for robust five-minute, offline-capable demonstration.

## 2. The Problem

- Bank teams receive fragmented, high-volume news and social signals.
- Manual triage is slow, inconsistent, and detached from portfolio action.
- Need: explainable, timely signals that downstream risk tools can consume.

## 3. Architecture

- Common source interface: RSS, optional Finnhub/social, and deterministic replay.
- Clean, deduplicate, normalize timestamps, detect language, and link entities.
- Local NLP derives sentiment, event type, confidence, and explainable impact.
- SQLite/JSONL persistence and FastAPI/SSE serve a unified dashboard.

## 4. Risk Signal Quality & Explainability

- Required outputs: sentiment [-1,1], event taxonomy, impact [1,10], confidence.
- Impact combines severity, sentiment magnitude, credibility, recency, and mention volume.
- Each factor is returned in the signal explanation—no opaque score.
- Seed benchmark: 86.0% sentiment accuracy / 0.854 macro F1; 94.0% event accuracy / 0.935 macro F1. Clearly labeled synthetic proxy.

## 5. Downstream Module A: Tactical Rebalancer

- 15-stock configurable S&P 100 universe, equal-weight baseline.
- Exponentially time-decayed sentiment tilts with confidence gating.
- Floor, cap, and turnover constraints make weights implementable.
- Dashboard links every allocation change back to its triggering signals.

## 6. Downstream Module B: Event-Driven Stress Testing

- Seeded 150-position, ~$1B wholesale portfolio: loans, bonds, derivatives, equities/FX.
- Scenario shocks scale with signal impact; valuation uses duration/convexity, PD×LGD×EAD, and delta/DV01 approximations.
- Breaking-news demo automatically creates a geopolitical signal and stress test; illustrated result: impact 7.84, P&L about -$39.3M.

## 7. Robustness, Roadmap & Ask

- Replay-first: live APIs fail safely without breaking the demo.
- Config-driven universe, sources, thresholds, mappings, and portfolio assumptions.
- Next: licensed production news, FinBERT/LLM model registry, real dated benchmark corpus, and bank model-risk validation.
- Ask: approve a pilot using authorized internal news and transaction data.
