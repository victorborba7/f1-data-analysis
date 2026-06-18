{#
    Qualifying fact. Grain: one row per driver per race qualifying session
    (qualifying_key). Q1/Q2/Q3 are kept as their raw lap-time strings; the
    best-of is parsed to seconds for sorting/aggregation.
#}

with qualifying as (
    select * from {{ ref('stg_jolpica__qualifying') }}
),

parsed as (
    select
        *,
        {{ laptime_to_seconds('q1_time') }} as q1_seconds,
        {{ laptime_to_seconds('q2_time') }} as q2_seconds,
        {{ laptime_to_seconds('q3_time') }} as q3_seconds
    from qualifying
)

select
    qualifying_key,
    race_key,
    driver_key,
    constructor_key,
    season_year,
    round_number,
    qualifying_position,
    q1_time,
    q2_time,
    q3_time,
    q1_seconds,
    q2_seconds,
    q3_seconds,
    nullif(
        least(
            coalesce(q3_seconds, 1e9),
            coalesce(q2_seconds, 1e9),
            coalesce(q1_seconds, 1e9)
        ),
        1e9
    ) as best_qualifying_seconds
from parsed
