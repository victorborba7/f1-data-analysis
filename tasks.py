#!/usr/bin/env python
"""
Cross-platform task runner for the F1 ELT pipeline (works on Windows + POSIX).

    python tasks.py backfill 1950:2026   # extract Jolpica history -> BigQuery raw
    python tasks.py refresh 2026          # re-pull one season (weekly)
    python tasks.py build                 # dbt deps + build (run + test) the marts
    python tasks.py test                  # dbt test only
    python tasks.py docs                  # dbt docs generate
    python tasks.py export                # marts -> serve/data/*.parquet
    python tasks.py tokens                # rebuild design tokens -> all surfaces
    python tasks.py preview               # quarto preview the site
    python tasks.py all 1950:2026         # backfill -> build -> docs -> export

Reads .env (if present) into the environment first.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSFORM = ROOT / "transform"


def load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def dbt(*args: str) -> None:
    run(["dbt", *args, "--profiles-dir", "."], cwd=TRANSFORM)


# -- tasks ------------------------------------------------------------------

def backfill(seasons: str = "1950:") -> None:
    run([sys.executable, "-m", "extract.pipeline", "backfill", "--seasons", seasons])


def refresh(season: str | None = None) -> None:
    args = [sys.executable, "-m", "extract.pipeline", "refresh"]
    if season:
        args += ["--season", season]
    run(args)


def build() -> None:
    dbt("deps")
    dbt("build")


def test() -> None:
    dbt("test")


def docs() -> None:
    dbt("docs", "generate")


def export() -> None:
    run([sys.executable, "-m", "extract.pipeline", "export"])


def tokens() -> None:
    run([sys.executable, str(ROOT / "design" / "build_tokens.py")])


def preview() -> None:
    run(["quarto", "preview"], cwd=ROOT)


def all_(seasons: str = "1950:") -> None:
    backfill(seasons)
    build()
    docs()
    export()


TASKS = {
    "backfill": backfill,
    "refresh": refresh,
    "build": build,
    "test": test,
    "docs": docs,
    "export": export,
    "tokens": tokens,
    "preview": preview,
    "all": all_,
}


def main() -> int:
    load_dotenv()
    if len(sys.argv) < 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        print("Tasks:", ", ".join(TASKS))
        return 1
    name, *rest = sys.argv[1:]
    try:
        TASKS[name](*rest)
    except subprocess.CalledProcessError as exc:
        print(f"\n✗ task '{name}' failed (exit {exc.returncode})")
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
