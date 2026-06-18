with source as (
    select * from {{ source('f1_raw', 'status') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['status']) }} as status_key,
    cast(status_id as int64)                           as status_id,
    status                                             as status_text,
    cast(count as int64)                               as occurrence_count
from source
