with source as (
    select * from {{ source('f1_raw', 'constructors') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['constructor_id']) }} as constructor_key,
    constructor_id,
    name                                                       as constructor_name,
    nationality,
    url                                                        as wikipedia_url
from source
