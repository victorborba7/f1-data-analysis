{#
    Final constructor-championship standing per season. Grain: constructor per
    season. The constructors' championship only began in 1958.
#}

with standings as (
    select * from {{ ref('stg_jolpica__constructor_standings') }}
)

select
    constructor_standing_key,
    season_key,
    constructor_key,
    season_year,
    final_round,
    championship_position,
    points,
    wins,
    championship_position = 1 as is_champion
from standings
