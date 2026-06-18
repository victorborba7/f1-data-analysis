{#
    Central fact: one row per driver per race. All flags/ordering come from
    int_results_enriched; this model just selects the presentation columns.
    Grain: result_key (season + round + driver).
#}

with enriched as (
    select * from {{ ref('int_results_enriched') }}
)

select
    result_key,
    -- foreign keys to the star
    race_key,
    driver_key,
    constructor_key,
    circuit_key,
    status_key,
    -- degenerate dimensions
    season_year,
    round_number,
    race_date,
    -- measures
    car_number,
    grid_position,
    finish_position,
    position_order,
    position_text,
    points,
    laps_completed,
    race_time_millis,
    fastest_lap_rank,
    fastest_lap_number,
    fastest_lap_time,
    -- flags
    is_classified_finish,
    is_win,
    is_podium,
    is_points_scorer,
    is_pole,
    is_dnf
from enriched
