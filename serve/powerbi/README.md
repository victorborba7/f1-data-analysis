# Power BI report

A Power BI dashboard over the `f1_analytics` star schema — the BI face of the
ELT pipeline.

- **[CONNECTION.md](CONNECTION.md)** — how to connect (live BigQuery or local
  Parquet), the relationships to build, and suggested report pages.
- **[measures.dax](measures.dax)** — the DAX measures to paste into a `_Measures`
  table.
- **`f1_analytics.pbix`** — author this in Power BI Desktop following the guide,
  then save it here.
- **`screenshot.png`** — a screenshot of the finished report (surfaced in the
  repo README).

The report is declared as a dbt **exposure** (`powerbi_f1_analytics`), so it shows
up in the dbt lineage graph downstream of the marts it depends on.
