"""
Load tidy DataFrames into the BigQuery ``f1_raw`` dataset, one table per
endpoint. This is the "L" in ELT — no transformation, just a faithful landing of
the extracted rows. dbt (``transform/``) does all modelling from here.

Auth uses Application Default Credentials: set ``GOOGLE_APPLICATION_CREDENTIALS``
to a service-account JSON key with *BigQuery Data Editor* + *BigQuery Job User*.
"""
from __future__ import annotations

import pandas as pd

from .config import Settings


def _bq():
    """Import google-cloud-bigquery lazily so the extract step works without it."""
    try:
        from google.cloud import bigquery
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError(
            "google-cloud-bigquery is not installed. Run "
            "`pip install -r requirements-elt.txt` before the load step."
        ) from exc
    return bigquery


def get_client(settings: Settings):
    bigquery = _bq()
    return bigquery.Client(project=settings.require_project(), location=settings.bq_location)


def ensure_dataset(settings: Settings, client=None) -> str:
    """Create the raw dataset if it does not exist; return its fully-qualified id."""
    bigquery = _bq()
    client = client or get_client(settings)
    dataset_id = f"{settings.require_project()}.{settings.bq_dataset_raw}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = settings.bq_location
    client.create_dataset(dataset, exists_ok=True)
    return dataset_id


def load_dataframe(settings: Settings, df: pd.DataFrame, table: str, client=None) -> int:
    """Replace ``f1_raw.<table>`` with ``df``. Returns the row count loaded."""
    bigquery = _bq()
    client = client or get_client(settings)
    table_id = f"{settings.require_project()}.{settings.bq_dataset_raw}.{table}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # wait for completion
    print(f"  → loaded {len(df):>6} rows into {settings.bq_dataset_raw}.{table}")
    return len(df)
