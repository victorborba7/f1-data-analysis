-- The crowned driver champion should hold the most points in that season's
-- final standings (ties are broken by wins, never against the points leader).
-- Returns any season where the champion does not have the max points.
with standings as (
    select * from {{ ref('fct_driver_standings') }}
),

season_max as (
    select season_year, max(points) as max_points
    from standings
    group by season_year
)

select
    s.season_year,
    s.points     as champion_points,
    m.max_points
from standings s
inner join season_max m using (season_year)
where s.is_champion
  and s.points < m.max_points
