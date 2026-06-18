with source as (
    select * from {{ source('f1_raw', 'constructor_standings') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['season', 'constructor_id']) }} as constructor_standing_key,
    {{ dbt_utils.generate_surrogate_key(['season']) }}                 as season_key,
    {{ dbt_utils.generate_surrogate_key(['constructor_id']) }}         as constructor_key,
    cast(season as int64)   as season_year,
    cast(round as int64)    as final_round,
    constructor_id,
    cast(position as int64) as championship_position,
    cast(points as float64) as points,
    cast(wins as int64)     as wins
from source
