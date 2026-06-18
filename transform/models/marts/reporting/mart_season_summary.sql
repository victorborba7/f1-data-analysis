{#
    One row per season: counts plus the crowned driver and constructor champions.
    Constructor champion is null before 1958.
#}

with results as (
    select * from {{ ref('fct_race_results') }}
),

season_counts as (
    select
        season_year,
        count(distinct race_key)        as races,
        count(distinct driver_key)      as drivers,
        count(distinct constructor_key) as constructors
    from results
    group by season_year
),

driver_champion as (
    select s.season_year, d.full_name as champion_driver
    from {{ ref('fct_driver_standings') }} s
    inner join {{ ref('dim_driver') }} d using (driver_key)
    where s.is_champion
),

constructor_champion as (
    select s.season_year, c.constructor_name as champion_constructor
    from {{ ref('fct_constructor_standings') }} s
    inner join {{ ref('dim_constructor') }} c using (constructor_key)
    where s.is_champion
)

select
    sc.season_year,
    sc.races,
    sc.drivers,
    sc.constructors,
    dc.champion_driver,
    cc.champion_constructor
from season_counts sc
left join driver_champion dc using (season_year)
left join constructor_champion cc using (season_year)
order by sc.season_year
