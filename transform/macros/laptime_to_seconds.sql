{#
    Convert an F1 lap-time string ("1:29.179" or "59.812") into float seconds.
    Returns null for null/blank input. Assumes at most minutes:seconds.millis
    (qualifying/lap times never reach an hour).
#}
{% macro laptime_to_seconds(column) -%}
case
    when {{ column }} is null or {{ column }} = '' then null
    when strpos({{ column }}, ':') > 0 then
        cast(split({{ column }}, ':')[offset(0)] as float64) * 60
        + cast(split({{ column }}, ':')[offset(1)] as float64)
    else cast({{ column }} as float64)
end
{%- endmacro %}
