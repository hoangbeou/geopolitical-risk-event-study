# Executive Decision Memo — Geopolitical Shock Response (2015–2025)

**Project**: Geopolitical risk (GPR) → asset price reaction (BTC / Gold / WTI Oil)  
**Method**: Event Study, event window \[-10, +10\], estimation window 120 trading days, Patell Z-test  
**Dataset**: 63 GPR events (auto-detected + Wikipedia enriched), 2015–10/2025

---

## 1) Business problem

Geopolitical shocks transmit into markets via supply disruption, inflation pressure, and risk sentiment. The decision problem is:

- **Which asset reacts consistently** to GPR shocks (actionable hedging signal)?
- Which asset shows **short-lived spikes** (tactical only)?
- Does Bitcoin behave like “digital gold”, or is it **context-dependent / speculative**?

---

## 2) What we measured (decision-relevant metrics)

- **CAAR**: average cumulative abnormal return in \[-10, +10\] around each event  
- **Significance**: Patell Z + p-value (is the effect systematic vs noise?)  
- **Time-decay**: when the reaction starts (anticipatory), peaks (T0/T+1), and fades  
- **Segmentation**: **ACT vs THREAT** and **geography** (oil-producing regions vs others)

---

## 3) Key findings (insights)

### Gold — consistent, statistically significant, and persistent
- **CAAR ≈ +0.34%**, **p < 0.001** (strong evidence of systematic positive reaction)
- Reaction builds early (**~T-5**) and persists **~5–7 days** post-event  
**Interpretation**: Gold acts as a reliable “risk-off” absorber when geopolitical uncertainty rises.

### Oil — large shocks but short-lived and geography-sensitive
- **CAAR ≈ +0.69%**, but **not statistically significant** (high volatility, mixed outcomes)
- Spike is typically **T0–T+1**, then mean-reverts after **~T+3**
- Stronger response when events are near **oil-supply regions**  
**Interpretation**: Oil is better treated as **tactical exposure** tied to supply risk, not a stable hedge.

### Bitcoin — polarized response; aggregation hides the signal
- Overall CAAR is **not significant** when pooling all events
- But segmentation shows a **cancellation effect**:
  - **ACT** events: **+4.08%**
  - **THREAT** events: **-4.40%**
**Interpretation**: Bitcoin is **not a consistent hedge**; it behaves like a high-beta, regime-sensitive asset. You must segment by event type to avoid misleading conclusions.

---

## 4) Recommended decision rules (portfolio playbook)

These rules convert findings into “if/then” actions for a risk/PM workflow.

1. **If GPR shock is THREAT-dominant** (uncertainty spike):
   - Prefer **Gold** allocation/overlay (more systematic response; uncertainty-averse channel).
   - Avoid treating BTC as hedge (negative average in THREAT group, high dispersion).

2. **If GPR shock is ACT-dominant AND tied to oil-supply geography**:
   - Consider **Oil** tactical position (expect spike around T0–T+1).
   - Use a **time-based exit** (e.g., reassess/trim after T+3 due to mean reversion).

3. **For Bitcoin exposure**:
   - Treat as **risk-on/speculative**; only consider opportunistic positioning under ACT regimes.
   - Require stricter risk controls (position sizing, drawdown limits) due to extreme tails.

---

## 5) Risks & limitations (what could break the rules)

- **Event clustering**: multiple shocks close in time can contaminate windows.
- **Wikipedia enrichment noise**: incomplete/ambiguous event descriptions for some dates.
- **Window choice**: \[-10, +10\] captures short-term action; longer macro effects not modeled here.
- **Non-stationary market regimes**: crypto market structure changes over 2015–2025.

---

## 6) Deliverables (for stakeholders)

- Event list (auto-detected spikes/high-periods + enriched names/locations)
- CAAR tables + significance tests (overall + ACT/THREAT + geography)
- Time-decay charts (AAR/CAAR per day)
- “Playbook rules” above for PM/risk operations

