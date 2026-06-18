with source as (
    select * from {{ source('f1_raw', 'results') }}
)

select
    -- natural + foreign keys
    {{ dbt_utils.generate_surrogate_key(['season', 'round', 'driver_id']) }} as result_key,
    {{ dbt_utils.generate_surrogate_key(['season', 'round']) }}             as race_key,
    {{ dbt_utils.generate_surrogate_key(['driver_id']) }}                   as driver_key,
    {{ dbt_utils.generate_surrogate_key(['constructor_id']) }}              as constructor_key,
    {{ dbt_utils.generate_surrogate_key(['status']) }}                      as status_key,
    cast(season as int64)        as season_year,
    cast(round as int64)         as round_number,
    driver_id,
    constructor_id,
    -- measures / attributes
    cast(car_number as int64)    as car_number,
    cast(grid as int64)          as grid_position,
    cast(position as int64)      as finish_position,
    position_text,
    cast(points as float64)      as points,
    cast(laps as int64)          as laps_completed,
    status                       as status_text,
    cast(time_millis as int64)   as race_time_millis,
    cast(fastest_lap_rank as int64)   as fastest_lap_rank,
    cast(fastest_lap_number as int64) as fastest_lap_number,
    fastest_lap_time
from source
-- A handful of 1950s "shared drive" races classify the same driver in two cars
-- (e.g. Ascari in two Ferraris at the 1950 Italian GP). Keep one row per driver
-- per race — their primary/best classification — so the grain stays unique and
-- career rollups don't double-count entries.
qualify row_number() over (
    partition by season, round, driver_id
    order by safe_cast(position as int64) asc, position_text asc
) = 1
