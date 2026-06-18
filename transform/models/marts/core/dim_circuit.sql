with circuits as (
    select * from {{ ref('stg_jolpica__circuits') }}
)

select
    circuit_key,
    circuit_id,
    circuit_name,
    locality,
    country,
    latitude,
    longitude,
    wikipedia_url
from circuits
