with source as (
    select * from {{ source('f1_raw', 'seasons') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['season']) }} as season_key,
    cast(season as int64)                              as season_year,
    url                                                as wikipedia_url
from source
