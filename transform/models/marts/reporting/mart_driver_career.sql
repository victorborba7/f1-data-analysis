{#
    One row per driver: a career rollup of the race-results fact, enriched with
    championship counts from the standings fact and names from the driver dim.
    Feeds the Quarto "All-Time Leaders" page and Power BI.
#}

with results as (
    select * from {{ ref('fct_race_results') }}
),

career as (
    select
        driver_key,
        count(*)                                as race_entries,
        countif(is_win)                         as wins,
        countif(is_podium)                      as podiums,
        countif(is_pole)                        as poles,
        countif(is_points_scorer)               as points_finishes,
        countif(is_dnf)                          as dnfs,
        sum(points)                             as career_points,
        min(season_year)                        as first_season,
        max(season_year)                        as last_season,
        count(distinct season_year)             as seasons_contested
    from results
    group by driver_key
),

titles as (
    select driver_key, countif(is_champion) as championships
    from {{ ref('fct_driver_standings') }}
    group by driver_key
)

select
    d.driver_key,
    d.driver_id,
    d.full_name,
    d.driver_code,
    d.nationality,
    career.first_season,
    career.last_season,
    career.seasons_contested,
    career.race_entries,
    coalesce(titles.championships, 0) as championships,
    career.wins,
    career.podiums,
    career.poles,
    career.points_finishes,
    career.dnfs,
    career.career_points,
    round(safe_divide(career.wins, career.race_entries), 4)    as win_rate,
    round(safe_divide(career.podiums, career.race_entries), 4) as podium_rate
from career
inner join {{ ref('dim_driver') }} d using (driver_key)
left join titles using (driver_key)
