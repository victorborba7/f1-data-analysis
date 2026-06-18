"""
Extract + Load layer of the F1 ELT pipeline.

Pulls Formula 1 history from the Jolpica-F1 API (the Ergast successor) and lands
it, table-per-endpoint, into the BigQuery ``f1_raw`` dataset. The dbt project in
``transform/`` takes over from there.

Entry point: ``python -m extract.pipeline --help``.
"""
