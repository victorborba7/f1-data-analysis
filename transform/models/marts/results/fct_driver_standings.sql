{#
    Final driver-championship standing per season. Grain: driver per season.
#}

with standings as (
    select * from {{ ref('stg_jolpica__driver_standings') }}
)

select
    driver_standing_key,
    season_key,
    driver_key,
    constructor_key,
    season_year,
    final_round,
    championship_position,
    points,
    wins,
    championship_position = 1 as is_champion
from standings
