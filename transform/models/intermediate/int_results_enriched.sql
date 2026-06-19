{#
    Resolve every race result to its surrogate keys (pulling circuit + date from
    the race) and derive the boolean flags and ordering that several marts reuse.
    Kept ephemeral: it compiles into the models that select from it.
#}

with results as (
    select * from {{ ref('stg_jolpica__results') }}
),

races as (
    select race_key, circuit_key, race_date from {{ ref('stg_jolpica__races') }}
)

select
    r.result_key,
    r.race_key,
    r.driver_key,
    r.constructor_key,
    races.circuit_key,
    r.status_key,
    r.season_year,
    r.round_number,
    races.race_date,
    r.driver_id,
    r.constructor_id,

    -- measures
    r.car_number,
    r.grid_position,
    r.finish_position,
    r.position_text,
    r.points,
    r.laps_completed,
    r.race_time_millis,
    r.fastest_lap_rank,
    r.fastest_lap_number,
    r.fastest_lap_time,
    r.status_text,

    -- a clean sort key so DNFs (null finish_position) order last
    coalesce(r.finish_position, 999)                       as position_order,

    -- derived flags
    r.status_text = 'Finished'                             as is_classified_finish,
    r.finish_position = 1                                  as is_win,
    r.finish_position <= 3                                 as is_podium,
    r.grid_position = 1                                    as is_pole,
    coalesce(r.points, 0) > 0                              as is_points_scorer,
    case
        when r.status_text = 'Finished' then false
        when r.status_text like '+%Lap%' then false
        else true
    end                                                    as is_dnf
from results r
left join races using (race_key)
