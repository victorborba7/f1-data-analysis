-- Every season must crown exactly one driver champion. Returns offending
-- seasons; an empty result means the test passes.
select
    season_year,
    count(*) as champion_count
from {{ ref('fct_driver_standings') }}
where is_champion
group by season_year
having count(*) <> 1
