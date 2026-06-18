# warehouse/ — BigQuery datasets

The warehouse is **BigQuery** (no local DB file). Three datasets make up the
medallion-style layout; all are created automatically — there's nothing to run
here by hand.

| Dataset | Created by | Contents |
|---------|-----------|----------|
| `f1_raw` | `extract/load_bigquery.py` (`ensure_dataset`) | Raw, table-per-endpoint landing zone |
| `f1_staging` | dbt | Staging views + the `seed_status_group` seed |
| `f1_analytics` | dbt | The dimensional marts (star schema) |

Dataset names and location come from environment variables (`BQ_DATASET_RAW`,
`BQ_DATASET_ANALYTICS`, `BQ_LOCATION`) — see [`../.env.example`](../.env.example).

### First-time GCP setup

1. Create (or pick) a GCP project and enable the **BigQuery API**.
2. Create a service account with **BigQuery Data Editor** + **BigQuery Job User**.
3. Download its JSON key; point `GOOGLE_APPLICATION_CREDENTIALS` at it in `.env`.
4. Run `python tasks.py all` — the datasets and tables are created as needed.

> Want a different warehouse? The dbt project is standard; swapping `profiles.yml`
> to another adapter (e.g. DuckDB or Snowflake) and re-pointing the loader is the
> only change. BigQuery was chosen here to demonstrate a cloud warehouse.
