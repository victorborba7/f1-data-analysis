with source as (
    select * from {{ source('f1_raw', 'races') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['season', 'round']) }} as race_key,
    {{ dbt_utils.generate_surrogate_key(['season']) }}         as season_key,
    {{ dbt_utils.generate_surrogate_key(['circuit_id']) }}     as circuit_key,
    cast(season as int64)                                      as season_year,
    cast(round as int64)                                       as round_number,
    race_name,
    circuit_id,
    cast(date as date)                                         as race_date,
    time                                                       as race_time_utc,
    url                                                        as wikipedia_url
from source
