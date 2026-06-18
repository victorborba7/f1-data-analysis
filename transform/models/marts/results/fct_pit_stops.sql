{#
    Pit-stop fact (2011 onward). Grain: one row per driver per stop per race.
#}

with pit_stops as (
    select * from {{ ref('stg_jolpica__pit_stops') }}
)

select
    pit_stop_key,
    race_key,
    driver_key,
    season_year,
    round_number,
    stop_number,
    lap_number,
    time_of_day,
    duration_seconds
from pit_stops
