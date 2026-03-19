-- Feature engineering: log-returns and first differences
-- Output: view v_features

create schema if not exists gpr_project;
set search_path = gpr_project, public;

drop view if exists v_features cascade;

create view v_features as
with base as (
  select
    dt,
    btc,
    gold,
    oil,
    -- Prefer GPRD if present (matches thesis naming), else fallback to GPR
    coalesce(gprd, gpr) as gpr_level,
    gpr_act,
    gpr_threat
  from raw_daily
),
features as (
  select
    dt,
    btc,
    gold,
    oil,
    gpr_level,
    gpr_act,
    gpr_threat,

    -- log returns (NULL if missing previous)
    ln(btc / nullif(lag(btc) over (order by dt), 0))  as btc_ret,
    ln(gold / nullif(lag(gold) over (order by dt), 0)) as gold_ret,
    ln(oil / nullif(lag(oil) over (order by dt), 0))   as oil_ret,

    -- first difference for GPR level
    (gpr_level - lag(gpr_level) over (order by dt)) as gpr_diff
  from base
)
select *
from features
where extract(isodow from dt) between 1 and 5; -- Mon..Fri (keeps it finance-friendly)

