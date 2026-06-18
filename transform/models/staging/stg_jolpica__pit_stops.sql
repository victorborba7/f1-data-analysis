with source as (
    select * from {{ source('f1_raw', 'pit_stops') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['season', 'round', 'driver_id', 'stop']) }} as pit_stop_key,
    {{ dbt_utils.generate_surrogate_key(['season', 'round']) }}                     as race_key,
    {{ dbt_utils.generate_surrogate_key(['driver_id']) }}                           as driver_key,
    cast(season as int64)    as season_year,
    cast(round as int64)     as round_number,
    driver_id,
    cast(stop as int64)      as stop_number,
    cast(lap as int64)       as lap_number,
    time_of_day,
    cast(duration_s as float64) as duration_seconds
from source
