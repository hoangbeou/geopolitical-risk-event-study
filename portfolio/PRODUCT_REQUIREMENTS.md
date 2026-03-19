# Product Requirements (BA) — GPR Shock Monitor

**Product concept**: A monitoring + alerting layer that detects major geopolitical risk (GPR) shocks and translates them into **actionable risk signals** for a portfolio team.

---

## 1) Problem statement

Portfolio/risk teams need **fast, consistent** interpretation of geopolitical risk spikes. Today, responses are often ad-hoc (news-driven), leading to inconsistent hedging and missed timing (time-decay).

---

## 2) Goals & non-goals

### Goals
- Detect major GPR events automatically (spike + high-period).
- Classify events into **ACT vs THREAT** and attach **location/region**.
- Provide “expected reaction templates” for **Gold / Oil / BTC** based on empirical time-decay patterns.
- Offer dashboards and alerts for portfolio decision workflows.

### Non-goals
- Predict long-run macro outcomes of wars (beyond short event window).
- Replace full quant trading systems (this is a monitoring + decision-support tool).

---

## 3) Personas

- **Portfolio Manager (PM)**: needs quick “what to do” summary and timing guidance.
- **Risk Officer**: needs consistent thresholds, auditability, false-positive control.
- **Research Analyst**: needs drill-down, event metadata, and ability to export datasets.

---

## 4) User stories (MVP)

### Detection & classification
- As a Risk Officer, I want alerts when **GPR_diff exceeds the 95th percentile**, so I can flag shock days.
- As a Research Analyst, I want “high-period” detection (≥5 consecutive high-GPR days), so prolonged risk regimes are not missed.
- As a PM, I want each event labeled **ACT vs THREAT**, so I can apply different playbooks (BTC polarization).
- As a PM, I want each event tagged with **region**, so I can interpret Oil vs non-Oil geography sensitivity.

### Dashboard & decision support
- As a PM, I want a dashboard showing **GPR + event markers + expected asset reaction windows (T-5…T+7)**.
- As a PM, I want a suggested action template per asset:
  - Gold: anticipatory build + persistence
  - Oil: spike + mean reversion
  - BTC: regime-dependent (ACT vs THREAT)

### Export & audit
- As a Research Analyst, I want to export event tables and features to CSV for further analysis.
- As a Risk Officer, I want alert rules to be transparent and reproducible (SQL scripts + versioned thresholds).

---

## 5) Functional requirements

### FR1 — Data ingestion
- Ingest daily GPR (level + ACT + THREAT) and daily close prices for BTC, Gold, Oil.
- Store in a single date-indexed table/view.

### FR2 — Feature engineering
- Compute:
  - BTC/GOLD/OIL **log returns**
  - `gpr_diff` (first difference)

### FR3 — Event detection
- Spike detection:
  - `gpr_diff > P95(gpr_diff)` and `gpr_diff > 0`
  - deconflict: keep events at least 30 days apart
- High-period detection:
  - `gpr_level > P95(gpr_level)` islands with length ≥ 5 trading days
  - choose event date = argmax(`gpr_diff`) in the island, require `gpr_diff > 0`

### FR4 — Enrichment
- Attach `event_name`, `location` from Wikipedia sources (if available).
- Map `location` → `region`.

### FR5 — Classification
- Label event type:
  - ACT vs THREAT using relative strength of GPR_ACT vs GPR_THREAT.

### FR6 — Reporting outputs
- Produce:
  - `events_final` (canonical event table)
  - `events_enriched`
  - `events_classified_act_threat`

---

## 6) Non-functional requirements

- **Explainability**: every alert must show threshold values and why it triggered.
- **Reproducibility**: SQL scripts versioned; parameters documented.
- **Latency**: daily batch OK (EOD), optional intraday enhancement later.
- **Data quality**: missing values handled deterministically; monitoring for gaps.

---

## 7) KPIs / success metrics

- **Precision of detected events**: % detected events that map to real-world conflicts (spot-check sample).
- **False positive rate**: % alerts with weak/irrelevant context.
- **Timeliness**: time from GPR spike to alert delivery.
- **Adoption**: weekly active PM/Risk users, exported reports count.

---

## 8) MVP dashboard spec (high-level)

### Tabs
1. **Overview**
   - GPR time series, event markers, filter by ACT/THREAT
2. **Event detail**
   - event metadata, location/region, GPR_ACT vs GPR_THREAT
3. **Asset reaction templates**
   - Gold/Oil/BTC “expected reaction window” (time-decay)
4. **Exports**
   - download events/features tables

