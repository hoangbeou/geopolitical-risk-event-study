# SQL Case Study (PostgreSQL) — Features & Event Detection

Mục tiêu của case study này là “đóng gói” 2 phần phù hợp CV BA/Data:

1) **Feature engineering** trên chuỗi thời gian (log-return, first difference)  
2) **Rule-based event detection** (spike + high-period) bằng SQL (window functions + gaps & islands)

---

## 1) Business context

Để chạy Event Study, cần một bảng sự kiện `T0` đáng tin cậy và một bộ feature tối thiểu:

- `btc_ret`, `gold_ret`, `oil_ret` (log returns)
- `gpr_diff` (đột biến GPR)

Thay vì xử lý hoàn toàn trong Python, phần này được chuyển sang SQL để:

- dễ audit & giải thích với stakeholder,
- tái lập (reproducible) trong pipeline ETL,
- thể hiện năng lực SQL cho portfolio.

---

## 2) Data model (SQL objects)

Các file SQL nằm tại:

- `pipeline/sql/00_schema_and_load.sql`
- `pipeline/sql/01_features.sql`
- `pipeline/sql/02_detect_events.sql`

### Tables / Views tạo ra

- `gpr_project.raw_daily` (table): daily prices + GPR levels
- `gpr_project.v_features` (view): prices + log-returns + `gpr_diff`
- `gpr_project.v_event_candidates_spike` (view)
- `gpr_project.v_event_candidates_high_period` (view)
- `gpr_project.events_final` (table): merged + deconflict 30 ngày

---

## 3) Feature engineering (what SQL does)

Trong `v_features`:

- **Log returns**:
  - `ln(price / lag(price))`
- **GPR_diff**:
  - `gpr_level - lag(gpr_level)`
- **Finance-friendly filter**:
  - Giữ Mon–Fri để giảm nhiễu non-trading days.

Kỹ thuật chính:
- `LAG(...) OVER (ORDER BY dt)`  
- `NULLIF(...)` tránh chia cho 0

---

## 4) Event detection logic (SQL rules)

### 4.1 Spike events

Rule:
- `gpr_diff > P95(gpr_diff)`
- `gpr_diff > 0`

Kỹ thuật:
- `percentile_cont(0.95) within group (order by ...)`

### 4.2 High-period events (gaps & islands)

Rule:
- `gpr_level > P95(gpr_level)` liên tiếp **≥ 5 ngày**
- chọn `event_date` là ngày có **max(gpr_diff)** trong mỗi island
- yêu cầu `gpr_diff > 0`

Kỹ thuật:
- “Islands” bằng:
  - `dt - row_number()` → khoá island ổn định theo block liên tiếp
- Ranking:
  - `row_number() over (partition by island_key order by gpr_diff desc)`

### 4.3 Deconflict 30 ngày

Mục tiêu: tránh chọn 2 event quá gần nhau.  
Triển khai:
- Gom candidate events (spike + high-period)
- Sắp xếp theo `gpr_diff` giảm dần
- Chọn theo **greedy** bằng recursive CTE: chỉ nhận event nếu cách các event đã chọn > 30 ngày

Kỹ thuật:
- `WITH RECURSIVE ...`
- `array[...]` + `unnest(...)` để kiểm tra khoảng cách ngày

---

## 5) Output & how it feeds the pipeline

- `events_final` là bảng “chuẩn hoá” để downstream dùng cho:
  - enrichment (Wikipedia, location/region)
  - Event Study (AR/CAR/CAAR)

---

## 6) CV bullets (copy/paste)

- Implemented **time-series feature engineering** in PostgreSQL using window functions (`LAG`) to compute **log-returns** for BTC/Gold/Oil and **first-difference** for GPR.
- Built a **rule-based GPR event detector** in SQL: spike detection via **95th percentile thresholds** and high-period detection via **gaps-and-islands** segmentation.
- Produced an auditable `events_final` table with **30-day deconfliction** (recursive CTE), enabling downstream event-study analysis and reporting.

