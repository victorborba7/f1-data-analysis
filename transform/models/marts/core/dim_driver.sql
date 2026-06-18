with drivers as (
    select * from {{ ref('stg_jolpica__drivers') }}
)

select
    driver_key,
    driver_id,
    driver_code,
    permanent_number,
    given_name,
    family_name,
    full_name,
    date_of_birth,
    nationality,
    wikipedia_url
from drivers
