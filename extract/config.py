"""
Central configuration for the extract/load layer, sourced from environment
variables (see ``.env.example``). Importing this module never touches the
network or BigQuery — it just resolves settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Repo root = parent of the extract/ package.
REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """
    Minimal .env loader (no dependency). Runs at import, before any os.getenv
    below, so `python -m extract.pipeline` honors .env without a manual export.
    Real environment variables take precedence (setdefault never overwrites).
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(REPO_ROOT / ".env")

# Jolpica-F1 (Ergast-compatible successor). Ergast itself was shut down in 2025.
JOLPICA_BASE_URL = os.getenv("JOLPICA_BASE_URL", "https://api.jolpi.ca/ergast/f1")

# Documented Jolpica limits: 4 requests/second, 500/hour. We stay comfortably
# under the per-second cap; the on-disk cache makes the hourly cap a non-issue on
# re-runs because cached pages never hit the network.
JOLPICA_MIN_INTERVAL_S = float(os.getenv("JOLPICA_MIN_INTERVAL_S", "0.27"))
JOLPICA_PAGE_SIZE = int(os.getenv("JOLPICA_PAGE_SIZE", "100"))  # Jolpica max page

# First season with finishing-status data; pit stops only exist from 2011.
FIRST_SEASON = int(os.getenv("F1_FIRST_SEASON", "1950"))
PITSTOPS_FIRST_SEASON = int(os.getenv("F1_PITSTOPS_FIRST_SEASON", "2011"))


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings for an extract/load run."""

    gcp_project: str | None = os.getenv("GCP_PROJECT")
    bq_dataset_raw: str = os.getenv("BQ_DATASET_RAW", "f1_raw")
    bq_dataset_analytics: str = os.getenv("BQ_DATASET_ANALYTICS", "f1_analytics")
    bq_location: str = os.getenv("BQ_LOCATION", "US")
    base_url: str = JOLPICA_BASE_URL
    cache_dir: Path = field(default_factory=lambda: REPO_ROOT / "extract" / ".cache")
    page_size: int = JOLPICA_PAGE_SIZE
    min_interval_s: float = JOLPICA_MIN_INTERVAL_S

    def require_project(self) -> str:
        if not self.gcp_project:
            raise RuntimeError(
                "GCP_PROJECT is not set. Copy .env.example to .env and fill it in, "
                "or export GCP_PROJECT before running the load step."
            )
        return self.gcp_project


def get_settings() -> Settings:
    return Settings()
