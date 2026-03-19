-- PostgreSQL schema + load helper for data/data.csv
-- Assumes repo has data/data.csv created by pipeline.

begin;

create schema if not exists gpr_project;
set search_path = gpr_project, public;

drop table if exists raw_daily cascade;

create table raw_daily (
  dt date primary key,
  -- Prices (Close)
  btc double precision,
  gold double precision,
  oil double precision,
  -- GPR levels (columns may be null depending on your source file)
  gpr double precision,
  gprd double precision,
  gpr_act double precision,
  gpr_threat double precision
);

-- Load CSV
-- If your column names differ, adjust the mapping below or load to a staging table first.
--
-- Expected CSV structure: first column is DATE index, followed by BTC/GOLD/OIL and some GPR columns.
-- Pipeline writes date format dd/mm/yyyy; we parse it via datestyle.

set datestyle = 'ISO, DMY';

-- Staging to flexibly map columns by name
drop table if exists raw_daily_stage;
create table raw_daily_stage (
  date_text text,
  btc double precision,
  gold double precision,
  oil double precision,
  gpr double precision,
  gprd double precision,
  gpr_act double precision,
  gpr_threat double precision
);

-- IMPORTANT:
-- - This uses psql meta-command \copy (client-side). Run via `psql -f ...`.
-- - If your CSV has different headers, either edit the column list after WITH (FORMAT csv, HEADER true)
--   or load to raw_daily_stage with fewer columns.
\copy raw_daily_stage from 'data/data.csv' with (format csv, header true);

insert into raw_daily (dt, btc, gold, oil, gpr, gprd, gpr_act, gpr_threat)
select
  to_date(date_text, 'DD/MM/YYYY') as dt,
  btc,
  gold,
  oil,
  gpr,
  gprd,
  gpr_act,
  gpr_threat
from raw_daily_stage
where date_text is not null;

drop table raw_daily_stage;

commit;

