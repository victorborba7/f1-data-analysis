with source as (
    select * from {{ source('f1_raw', 'drivers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['driver_id']) }} as driver_key,
    driver_id,
    code                                                  as driver_code,
    cast(permanent_number as int64)                       as permanent_number,
    given_name,
    family_name,
    concat(given_name, ' ', family_name)                  as full_name,
    cast(date_of_birth as date)                           as date_of_birth,
    nationality,
    url                                                   as wikipedia_url
from source
