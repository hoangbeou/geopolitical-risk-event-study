# SQL version (PostgreSQL)

Mục tiêu: chuyển 2 phần “đẹp CV” sang SQL:

- **(1) Feature engineering**: log-return BTC/GOLD/OIL, `gpr_diff`
- **(2) Event detection**: Spike + High-period (gaps & islands) + deconflict 30 ngày

## Yêu cầu

- PostgreSQL 13+ (khuyến nghị)
- File dữ liệu đầu vào: `data/data.csv` (tạo từ pipeline ingest)

## Chạy nhanh (psql)

Trong repo root:

```bash
psql -d <your_db> -f pipeline/sql/00_schema_and_load.sql
psql -d <your_db> -f pipeline/sql/01_features.sql
psql -d <your_db> -f pipeline/sql/02_detect_events.sql
```

Sau đó xem kết quả:

```sql
select * from v_features limit 20;
select * from v_event_candidates_spike order by gpr_diff desc limit 20;
select * from v_event_candidates_high_period order by event_date desc limit 20;
select * from events_final order by event_date;
```

> Ghi chú: các script này ưu tiên **tính minh bạch & khả năng trình bày trong portfolio**. Nếu muốn tối ưu hiệu năng, có thể materialize view hoặc thêm index.

