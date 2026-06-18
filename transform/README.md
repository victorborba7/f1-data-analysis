# transform/ — dbt project

The analytics-engineering core. Turns the raw Jolpica tables in BigQuery
(`f1_raw`) into a tested, documented **star schema** in `f1_analytics`.

## Layers

| Path | Layer | Materialized |
|------|-------|--------------|
| `models/staging/` | Typed, renamed, surrogate-keyed views, 1:1 with source | views (`f1_staging`) |
| `models/intermediate/` | `int_results_enriched` — resolves keys, derives flags | ephemeral |
| `models/marts/core/` | Conformed dimensions | tables (`f1_analytics`) |
| `models/marts/results/` | Fact tables | tables (`f1_analytics`) |
| `models/marts/reporting/` | Career/season rollups for the serve layer | tables (`f1_analytics`) |

## Run it

```bash
# env vars come from ../.env (GCP_PROJECT, BQ_DATASET_*, GOOGLE_APPLICATION_CREDENTIALS)
dbt deps
dbt build --profiles-dir .          # run + test everything
dbt docs generate --profiles-dir .  # lineage + exposures
dbt docs serve --profiles-dir .
```

`profiles.yml` lives in this folder and reads everything from the environment, so
no secrets are committed. The `generate_schema_name` macro lets models land in
clean dataset names (`f1_staging`, `f1_analytics`) rather than dbt's default
prefixed schemas.

## Tests

`dbt build` runs ~120 tests: key uniqueness/not-null, fact→dimension
`relationships`, `accepted_values`, value ranges (`dbt_expectations`), and two
singular tests under `tests/` for season-champion invariants.

Packages: `dbt_utils` (surrogate keys, generic tests) and `dbt_expectations`
(range/expectation tests) — see `packages.yml`.
