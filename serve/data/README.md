# serve/data

Parquet exports of the dbt **reporting marts**, produced by:

```bash
python -m extract.pipeline export
```

These files are **committed on purpose**: the Quarto site reads them at render
time, so the published site builds without BigQuery credentials (the same
"run locally, commit results" pattern the weekly `_freeze/` cache uses).

| File | Source mart |
|------|-------------|
| `mart_driver_career.parquet` | `mart_driver_career` |
| `mart_constructor_career.parquet` | `mart_constructor_career` |
| `mart_season_summary.parquet` | `mart_season_summary` |

Refresh them whenever the warehouse changes (e.g. after a new race), then commit.
