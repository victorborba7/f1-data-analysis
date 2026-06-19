with seasons as (
    select * from {{ ref('stg_jolpica__seasons') }}
)

select
    season_key,
    season_year,
    cast(floor(season_year / 10) * 10 as int64) as decade,
    case
        when season_year < 1980 then 'Early (1950–1979)'
        when season_year < 2000 then 'Turbo & V10 (1980–1999)'
        when season_year < 2014 then 'V8/V10 modern (2000–2013)'
        else 'Hybrid era (2014–)'
    end as era,
    wikipedia_url
from seasons
