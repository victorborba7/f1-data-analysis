with constructors as (
    select * from {{ ref('stg_jolpica__constructors') }}
)

select
    constructor_key,
    constructor_id,
    constructor_name,
    nationality,
    wikipedia_url
from constructors
