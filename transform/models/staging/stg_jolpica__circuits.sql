with source as (
    select * from {{ source('f1_raw', 'circuits') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['circuit_id']) }} as circuit_key,
    circuit_id,
    circuit_name,
    locality,
    country,
    cast(lat as float64)                                   as latitude,
    cast(lng as float64)                                   as longitude,
    url                                                    as wikipedia_url
from source
