"""
Command-line orchestrator for the extract/load layer.

    python -m extract.pipeline backfill --seasons 1950:2026
    python -m extract.pipeline refresh  --season 2026
    python -m extract.pipeline export   --tables mart_driver_career,mart_constructor_career

`backfill` / `refresh` pull from Jolpica and land raw tables in BigQuery.
`export` reads the dbt marts back out to serve/data/*.parquet for the Quarto site
and Power BI (so the published site builds without BigQuery credentials).
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from .config import PITSTOPS_FIRST_SEASON, FIRST_SEASON, REPO_ROOT, get_settings
from .jolpica import JolpicaClient, endpoints

STAGE_DIR = REPO_ROOT / "extract" / ".stage"
SERVE_DATA_DIR = REPO_ROOT / "serve" / "data"

# Reference dimensions are small, history-wide single collections.
REFERENCE_PULLERS = {
    "seasons": endpoints.pull_seasons,
    "circuits": endpoints.pull_circuits,
    "drivers": endpoints.pull_drivers,
    "constructors": endpoints.pull_constructors,
    "status": endpoints.pull_status,
    "races": endpoints.pull_races,
}

DEFAULT_EXPORT_TABLES = [
    "mart_driver_career",
    "mart_constructor_career",
    "mart_season_summary",
]


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract_all(client: JolpicaClient, seasons: list[int]) -> dict[str, pd.DataFrame]:
    """Pull every endpoint for ``seasons`` into a {table_name: DataFrame} map."""
    tables: dict[str, pd.DataFrame] = {}

    for name, puller in REFERENCE_PULLERS.items():
        print(f"· {name} …")
        tables[name] = puller(client)

    print("· results …")
    tables["results"] = endpoints.pull_results(client, seasons)
    print("· qualifying …")
    tables["qualifying"] = endpoints.pull_qualifying(client, seasons)
    print("· driver_standings …")
    tables["driver_standings"] = endpoints.pull_driver_standings(client, seasons)
    print("· constructor_standings …")
    tables["constructor_standings"] = endpoints.pull_constructor_standings(client, seasons)

    ps_seasons = [s for s in seasons if s >= PITSTOPS_FIRST_SEASON]
    if ps_seasons:
        print("· pit_stops …")
        tables["pit_stops"] = endpoints.pull_pit_stops(client, tables["races"], ps_seasons)

    return tables


def stage_local(tables: dict[str, pd.DataFrame]) -> None:
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(STAGE_DIR / f"{name}.parquet", index=False)
    print(f"Staged {len(tables)} tables → {STAGE_DIR}")


def load_to_bigquery(tables: dict[str, pd.DataFrame]) -> None:
    from . import load_bigquery as lbq

    settings = get_settings()
    client = lbq.get_client(settings)
    lbq.ensure_dataset(settings, client)
    print(f"Loading into {settings.gcp_project}.{settings.bq_dataset_raw} …")
    for name, df in tables.items():
        if df.empty:
            print(f"  · {name}: empty, skipped")
            continue
        lbq.load_dataframe(settings, df, name, client)


# ---------------------------------------------------------------------------
# Export (marts → parquet for the serve layer)
# ---------------------------------------------------------------------------

def export_marts(tables: list[str]) -> None:
    from . import load_bigquery as lbq

    settings = get_settings()
    client = lbq.get_client(settings)
    SERVE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for table in tables:
        table_id = f"{settings.require_project()}.{settings.bq_dataset_analytics}.{table}"
        df = client.query(f"SELECT * FROM `{table_id}`").to_dataframe()
        out = SERVE_DATA_DIR / f"{table}.parquet"
        df.to_parquet(out, index=False)
        print(f"  → exported {len(df):>6} rows  {table} → {out.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_seasons(spec: str) -> list[int]:
    """'1950:2026' -> [1950..2026]; '2026' -> [2026]; '2010:' -> [2010..now]."""
    this_year = dt.date.today().year
    if ":" in spec:
        lo, hi = spec.split(":", 1)
        start = int(lo) if lo else FIRST_SEASON
        end = int(hi) if hi else this_year
    else:
        start = end = int(spec)
    return list(range(start, end + 1))


def _run_extract(seasons: list[int], target: str, force: bool) -> None:
    client = JolpicaClient()
    if force:
        prefixes = [f"{s}_" for s in seasons] + list(REFERENCE_PULLERS)
        removed = client.clear_cache(*prefixes)
        print(f"Cleared {removed} cached pages (force refresh).")

    print(f"Seasons: {seasons[0]}–{seasons[-1]} ({len(seasons)} seasons)")
    tables = extract_all(client, seasons)
    print("\nRow counts:")
    for name, df in tables.items():
        print(f"  {name:<22} {len(df):>7}")

    if target in ("parquet", "both"):
        stage_local(tables)
    if target in ("bq", "both"):
        load_to_bigquery(tables)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="extract.pipeline", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_back = sub.add_parser("backfill", help="full or ranged historical load")
    p_back.add_argument("--seasons", default=f"{FIRST_SEASON}:",
                        help="e.g. 1950:2026, 2018:, or 2026")
    p_back.add_argument("--target", choices=["bq", "parquet", "both"], default="bq")

    p_ref = sub.add_parser("refresh", help="re-pull one season (e.g. weekly)")
    p_ref.add_argument("--season", type=int, default=dt.date.today().year)
    p_ref.add_argument("--target", choices=["bq", "parquet", "both"], default="bq")

    p_exp = sub.add_parser("export", help="dump dbt marts to serve/data/*.parquet")
    p_exp.add_argument("--tables", default=",".join(DEFAULT_EXPORT_TABLES))

    args = parser.parse_args(argv)

    if args.command == "backfill":
        _run_extract(parse_seasons(args.seasons), args.target, force=False)
    elif args.command == "refresh":
        _run_extract([args.season], args.target, force=True)
    elif args.command == "export":
        export_marts([t.strip() for t in args.tables.split(",") if t.strip()])


if __name__ == "__main__":
    main()
