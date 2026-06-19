with source as (
    select * from {{ source('f1_raw', 'qualifying') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['season', 'round', 'driver_id']) }} as qualifying_key,
    {{ dbt_utils.generate_surrogate_key(['season', 'round']) }}             as race_key,
    {{ dbt_utils.generate_surrogate_key(['driver_id']) }}                   as driver_key,
    {{ dbt_utils.generate_surrogate_key(['constructor_id']) }}              as constructor_key,
    cast(season as int64)   as season_year,
    cast(round as int64)    as round_number,
    driver_id,
    constructor_id,
    cast(position as int64) as qualifying_position,
    q1                      as q1_time,
    q2                      as q2_time,
    q3                      as q3_time
from source
