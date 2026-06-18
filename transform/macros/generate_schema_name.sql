{#
    Use custom schemas verbatim instead of dbt's default
    `<target_schema>_<custom_schema>` concatenation. This lets us land models in
    cleanly-named datasets (f1_staging, f1_analytics) regardless of the profile's
    default dataset. Models with no `+schema` fall back to the target dataset.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
