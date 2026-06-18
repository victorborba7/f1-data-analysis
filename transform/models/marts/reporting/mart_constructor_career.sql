{#
    One row per constructor: career rollup of results (per car entry) plus
    constructors'-championship counts. Race "wins" count winning cars, so a
    1-2 finish counts as one win via a distinct race count.
#}

with results as (
    select * from {{ ref('fct_race_results') }}
),

career as (
    select
        constructor_key,
        count(distinct race_key)                       as races_entered,
        count(distinct if(is_win, race_key, null))     as wins,
        countif(is_podium)                             as podium_finishes,
        countif(is_pole)                               as poles,
        sum(points)                                    as career_points,
        min(season_year)                               as first_season,
        max(season_year)                               as last_season,
        count(distinct season_year)                    as seasons_contested
    from results
    group by constructor_key
),

titles as (
    select constructor_key, countif(is_champion) as championships
    from {{ ref('fct_constructor_standings') }}
    group by constructor_key
)

select
    c.constructor_key,
    c.constructor_id,
    c.constructor_name,
    c.nationality,
    career.first_season,
    career.last_season,
    career.seasons_contested,
    career.races_entered,
    coalesce(titles.championships, 0) as championships,
    career.wins,
    career.podium_finishes,
    career.poles,
    career.career_points
from career
inner join {{ ref('dim_constructor') }} c using (constructor_key)
left join titles using (constructor_key)
