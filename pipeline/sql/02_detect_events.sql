-- Event detection (PostgreSQL)
-- - Spike: gpr_diff > p95(gpr_diff) and gpr_diff > 0
-- - High-period: "gpr_level > p95(gpr_level)" islands (>= 5 consecutive weekdays),
--   choose day with max gpr_diff inside each island, require gpr_diff > 0
-- - Deconflict: keep events at least 30 days apart (greedy by strongest signal)

create schema if not exists gpr_project;
set search_path = gpr_project, public;

drop view if exists v_thresholds cascade;
drop view if exists v_event_candidates_spike cascade;
drop view if exists v_event_candidates_high_period cascade;
drop table if exists events_final;

create view v_thresholds as
select
  percentile_cont(0.95) within group (order by gpr_diff)   as gpr_diff_p95,
  percentile_cont(0.95) within group (order by gpr_level)  as gpr_level_p95
from v_features
where gpr_diff is not null
  and gpr_level is not null;

create view v_event_candidates_spike as
select
  f.dt as event_date,
  f.gpr_diff,
  'spike'::text as method
from v_features f
cross join v_thresholds t
where f.gpr_diff is not null
  and f.gpr_diff > 0
  and f.gpr_diff > t.gpr_diff_p95;

-- High-period "islands" using gaps-and-islands on consecutive dates where gpr_level > p95
create view v_event_candidates_high_period as
with flagged as (
  select
    f.*,
    (f.gpr_level > t.gpr_level_p95) as is_high
  from v_features f
  cross join v_thresholds t
  where f.gpr_level is not null
),
high_only as (
  select
    dt,
    gpr_level,
    gpr_diff,
    -- island key: dt - row_number() gives constant value within consecutive blocks
    (dt - (row_number() over (order by dt))::int) as island_key
  from flagged
  where is_high
),
islands as (
  select
    island_key,
    count(*) as n_days
  from high_only
  group by island_key
  having count(*) >= 5
),
ranked as (
  select
    h.dt,
    h.gpr_diff,
    h.island_key,
    row_number() over (
      partition by h.island_key
      order by h.gpr_diff desc nulls last
    ) as rn
  from high_only h
  join islands i using (island_key)
)
select
  dt as event_date,
  gpr_diff,
  'high_period'::text as method
from ranked
where rn = 1
  and gpr_diff is not null
  and gpr_diff > 0;

-- Combine candidates and enforce minimum 30-day spacing (greedy by highest gpr_diff first)
create table events_final as
with candidates as (
  select * from v_event_candidates_spike
  union all
  select * from v_event_candidates_high_period
),
ranked as (
  select
    event_date,
    gpr_diff,
    method,
    row_number() over (order by gpr_diff desc, event_date asc) as rnk
  from candidates
),
-- Greedy selection via recursive CTE:
-- pick best remaining event, then exclude events within +/- 30 days, repeat.
recursive picked as (
  select
    r.event_date,
    r.gpr_diff,
    r.method,
    array[r.event_date] as picked_dates,
    r.rnk
  from ranked r
  where r.rnk = 1

  union all

  select
    r.event_date,
    r.gpr_diff,
    r.method,
    p.picked_dates || r.event_date,
    r.rnk
  from picked p
  join ranked r
    on r.rnk > p.rnk
  where not exists (
    select 1
    from unnest(p.picked_dates) d
    where abs(r.event_date - d) <= 30
  )
)
select distinct on (event_date)
  event_date,
  gpr_diff,
  method
from picked
order by event_date, gpr_diff desc;

create index if not exists idx_events_final_date on events_final(event_date);

