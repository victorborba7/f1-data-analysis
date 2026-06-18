{#
    The event dimension. Circuit attributes are denormalised in for BI
    convenience (so a race slicer carries country/locality without a second join).
#}

with races as (
    select * from {{ ref('stg_jolpica__races') }}
),

circuits as (
    select circuit_key, circuit_name, locality, country
    from {{ ref('stg_jolpica__circuits') }}
)

select
    races.race_key,
    races.season_key,
    races.circuit_key,
    races.season_year,
    races.round_number,
    races.race_name,
    races.race_date,
    extract(month from races.race_date) as race_month,
    circuits.circuit_name,
    circuits.locality,
    circuits.country,
    races.wikipedia_url
from races
left join circuits using (circuit_key)
