# Pipeline overview (Geopolitical Risk Event Study)

Tài liệu này mô tả pipeline theo thứ tự chạy và **artifact (file output)** ở mỗi bước.

> Lưu ý:
> - Source code Python đã được move vào `pipeline/*` (00→06).
> - Bạn cũng có nhánh **SQL (PostgreSQL)** cho bước 01–02 trong thư mục `sql/`.

---

## 00) Ingest (download + merge raw data)

- **Python script**: `pipeline/00_ingest/download_and_merge_data.py`
- **Input**:
  - Yahoo Finance (online): `BTC-USD`, `GC=F`, `CL=F`
  - GPR file (local, optional): `data/*gpr*.xls*` hoặc `data/*gpr*.csv`
- **Output**:
  - `data/data.csv` (merged, daily; date format dd/mm/yyyy)
  - (optional) `data/data_gpr_daily_recent.xlsx` nếu input GPR là Excel
- **Logic**:
  - Download close prices → outer join theo `DATE`
  - Join với GPR nếu tìm thấy file GPR trong `data/`
  - Không tính return ở bước này (chỉ ghép raw series)

---

## 01) Preprocess (returns + differences + alignment)

- **Có 2 cách chạy**:

### 01A) Python (pandas)

- **Module**: `src/preprocessing.py` (`DataPreprocessor`)
- **Input**: `data/data.csv`
- **Output**:
  - Trả ra DataFrame/Series trong memory (tuỳ script gọi)
  - Series quan trọng: `BTC_ret`, `GOLD_ret`, `OIL_ret`, `GPR_diff`
- **Logic**:
  - Log-return cho BTC/GOLD/OIL
  - Sai phân GPR → `GPR_diff`
  - Align theo ngày, dropna

### 01B) SQL (PostgreSQL) – *phiên bản để đưa vào CV*

- **SQL**:
  - `pipeline/sql/00_schema_and_load.sql` (tạo bảng `gpr_project.raw_daily` + load `data/data.csv`)
  - `pipeline/sql/01_features.sql` (tạo view `gpr_project.v_features`)
- **Output**:
  - `gpr_project.v_features` gồm: prices + `btc_ret`, `gold_ret`, `oil_ret`, `gpr_diff`

---

## 02) Event detection (spike + high-period)

- **Có 2 cách chạy**:

### 02A) Python

- **Python script**: `pipeline/02_event_detection/detect_events.py`
- **Input**:
  - `data/data.csv` (và/hoặc series `GPR_diff` được tạo trong code)
- **Output**:
  - CSV danh sách event date `T0` (tên file tuỳ config trong script)
- **Logic**:
  - Spike: `GPR_diff` > p95, `GPR_diff > 0`, cách nhau ≥ 30 ngày
  - High-period: `GPR` > p95 theo “period”, chọn ngày có `max(GPR_diff)`

### 02B) SQL (PostgreSQL) – *phiên bản để đưa vào CV*

- **SQL**: `pipeline/sql/02_detect_events.sql`
- **Input**: `gpr_project.v_features`
- **Output**:
  - `gpr_project.v_event_candidates_spike`
  - `gpr_project.v_event_candidates_high_period`
  - `gpr_project.events_final` (đã deconflict 30 ngày)

---

## 03) Enrichment (Wikipedia + location + region + ACT/THREAT)

- **Scripts**:
  - `pipeline/03_enrichment/enrich_events_with_locations.py` (Wikipedia: tên sự kiện, location)
  - `pipeline/03_enrichment/map_locations_to_region.py` (location → region)
  - `pipeline/03_enrichment/classify_act_threat.py` (ACT vs THREAT)
- **Input**:
  - Events detected (CSV từ bước 02)
  - (optional) mapping file / dictionary cho region
- **Output (thường gặp)**:
  - `results/events_enriched.csv`
  - `results/events_classified_act_threat.csv`

---

## 04) Event study (AR/CAR/CAAR + significance)

- **Python script**: `pipeline/04_event_study/run_event_study.py`
- **Input**:
  - `data/data.csv` (prices/returns)
  - Events classified (từ bước 03)
- **Output (thường gặp)**:
  - Bảng CAAR / p-value
  - File kết quả theo event window (CSV/MD) trong `results/`

---

## 05) Analysis (insights + ranking + plots)

- **Scripts** (tuỳ nhu cầu):
  - `pipeline/05_analysis/show_top_events.py`
  - `pipeline/05_analysis/analyze_top_events_by_asset.py`
  - `pipeline/05_analysis/generate_act_threat_insights.py`
  - `pipeline/05_analysis/generate_advanced_insights.py`
  - `pipeline/05_analysis/visualize_car_by_region.py`, `pipeline/05_analysis/visualize_patterns.py`
- **Input**:
  - Output từ bước 04 + file events classified
- **Output**:
  - Reports `.md` / tables / plots dưới `results/`

---

## 06) Reporting (tables + thesis build)

- **Scripts**:
  - `pipeline/06_reporting/generate_results_tables.py`
  - `pipeline/06_reporting/print_thesis_tables.py`
  - `pipeline/06_reporting/parse_event_study_results.py`
  - (optional) `pipeline/06_reporting/markdown_to_word.py`
- **Output**:
  - Tables cho luận văn / markdown report / export Word (nếu dùng)

