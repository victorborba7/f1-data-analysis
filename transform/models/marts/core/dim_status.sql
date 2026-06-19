{#
    Finishing-status dimension. The hand-maintained seed groups the common
    statuses; the parametric "+N Laps" values are grouped here in SQL, and
    anything unmapped falls back to 'Other'.
#}

with status as (
    select * from {{ ref('stg_jolpica__status') }}
),

status_groups as (
    select * from {{ ref('seed_status_group') }}
)

select
    status.status_key,
    status.status_id,
    status.status_text,
    status.occurrence_count,
    case
        when status.status_text like '+%Lap%' then 'Lapped'
        else coalesce(status_groups.status_group, 'Other')
    end as status_group
from status
left join status_groups on status.status_text = status_groups.status
