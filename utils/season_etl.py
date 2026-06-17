"""
Season-level ETL pipeline.

Ingests every completed race of a season into one tidy dataset, then derives
championship standings and teammate head-to-head battles. This is the
data-engineering layer: download once, model once, query many times.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import fastf1
import fastf1.plotting

from .f1_helpers import save_fig


# ---------------------------------------------------------------------------
# Extract + transform
# ---------------------------------------------------------------------------

def build_season_dataset(year: int, session_type: str = "R",
                         cache_path: str = "content/f1_cache",
                         data_dir: str = "data") -> pd.DataFrame:
    """
    Load every completed round of `year` and return a tidy results table.

    One row per driver per race. Skips rounds that aren't available yet
    (future races / testing). Persists to data/season_{year}.{parquet,csv}.
    """
    os.makedirs(cache_path, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path)

    schedule = fastf1.get_event_schedule(year)
    schedule = schedule[schedule["RoundNumber"] >= 1]

    records = []
    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        try:
            session = fastf1.get_session(year, rnd, session_type)
            session.load(telemetry=False, weather=False, messages=False)
        except Exception as exc:
            print(f"  · Round {rnd:>2} {event['EventName']}: skipped ({exc})")
            continue

        res = session.results
        if res is None or res.empty:
            print(f"  · Round {rnd:>2} {event['EventName']}: no results yet")
            continue

        for _, r in res.iterrows():
            records.append({
                "Year": year,
                "Round": rnd,
                "EventName": event["EventName"],
                "Country": event["Country"],
                "Driver": r.get("Abbreviation"),
                "FullName": r.get("FullName"),
                "Team": r.get("TeamName"),
                "Grid": pd.to_numeric(r.get("GridPosition"), errors="coerce"),
                "Position": pd.to_numeric(r.get("Position"), errors="coerce"),
                "Points": pd.to_numeric(r.get("Points"), errors="coerce"),
                "Status": r.get("Status"),
            })
        print(f"  ✓ Round {rnd:>2} {event['EventName']}: {len(res)} drivers")

    df = pd.DataFrame(records)
    if df.empty:
        print("No completed rounds found.")
        return df

    parquet_path = os.path.join(data_dir, f"season_{year}.parquet")
    csv_path = os.path.join(data_dir, f"season_{year}.csv")
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"\nSaved → {parquet_path}")
    except Exception:
        print("\n(parquet engine not installed — skipping .parquet)")
    df.to_csv(csv_path, index=False)
    print(f"Saved → {csv_path}")

    return df


def load_season_dataset(year: int, data_dir: str = "data") -> pd.DataFrame:
    """Load a previously built season dataset (parquet preferred, else csv)."""
    parquet_path = os.path.join(data_dir, f"season_{year}.parquet")
    csv_path = os.path.join(data_dir, f"season_{year}.csv")
    if os.path.exists(parquet_path):
        return pd.read_parquet(parquet_path)
    return pd.read_csv(csv_path)


# ---------------------------------------------------------------------------
# Derive: championship standings
# ---------------------------------------------------------------------------

def driver_standings(df: pd.DataFrame) -> pd.DataFrame:
    """Total points per driver, sorted (current championship order)."""
    standings = (df.groupby(["Driver", "Team"], as_index=False)["Points"]
                 .sum()
                 .sort_values("Points", ascending=False)
                 .reset_index(drop=True))
    standings.index += 1
    standings.index.name = "Pos"
    return standings


def constructor_standings(df: pd.DataFrame) -> pd.DataFrame:
    standings = (df.groupby("Team", as_index=False)["Points"]
                 .sum()
                 .sort_values("Points", ascending=False)
                 .reset_index(drop=True))
    standings.index += 1
    standings.index.name = "Pos"
    return standings


def cumulative_points(df: pd.DataFrame) -> pd.DataFrame:
    """Wide table: rows = round, columns = driver, values = cumulative points."""
    pivot = (df.pivot_table(index="Round", columns="Driver",
                            values="Points", aggfunc="sum")
             .fillna(0)
             .sort_index())
    return pivot.cumsum()


def plot_championship_progression(df: pd.DataFrame, top_n: int = 8,
                                  session=None, assets_path: str = "assets") -> plt.Figure:
    cum = cumulative_points(df)
    leaders = cum.iloc[-1].sort_values(ascending=False).head(top_n).index.tolist()

    # map driver -> team for colour
    drv_team = df.drop_duplicates("Driver").set_index("Driver")["Team"].to_dict()

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    for drv in leaders:
        try:
            color = fastf1.plotting.get_team_color(drv_team[drv], session=session)
        except Exception:
            color = None
        ax.plot(cum.index, cum[drv], marker="o", markersize=3, linewidth=1.8,
                color=color, label=f"{drv} ({int(cum[drv].iloc[-1])})")

    ax.set_xlabel("Round", color="white", fontsize=11)
    ax.set_ylabel("Cumulative Points", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#444")
    ax.grid(alpha=0.15, color="white")
    ax.legend(facecolor="#2a2a3e", labelcolor="white", fontsize=9, loc="upper left")
    year = int(df["Year"].iloc[0])
    ax.set_title(f"{year} Drivers' Championship — Points Progression",
                 color="white", fontsize=14, fontweight="bold", pad=12)

    plt.tight_layout()
    save_fig(fig, "S1_championship_progression.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Derive: teammate head-to-head
# ---------------------------------------------------------------------------

def teammate_battles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per team, head-to-head between its two drivers across all rounds:
    race finishes (who finished ahead), qualifying (grid), and total points.
    """
    rows = []
    for team, g in df.groupby("Team"):
        drivers = g["Driver"].dropna().unique()
        if len(drivers) != 2:
            continue  # skip teams with driver changes / reserves for clarity
        d1, d2 = drivers

        merged = g.pivot_table(index="Round", columns="Driver",
                               values=["Position", "Grid", "Points"], aggfunc="first")

        race_d1 = race_d2 = quali_d1 = quali_d2 = 0
        for rnd in merged.index:
            p1, p2 = merged.loc[rnd, ("Position", d1)], merged.loc[rnd, ("Position", d2)]
            if pd.notna(p1) and pd.notna(p2):
                race_d1 += int(p1 < p2)
                race_d2 += int(p2 < p1)
            q1, q2 = merged.loc[rnd, ("Grid", d1)], merged.loc[rnd, ("Grid", d2)]
            if pd.notna(q1) and pd.notna(q2):
                quali_d1 += int(q1 < q2)
                quali_d2 += int(q2 < q1)

        rows.append({
            "Team": team,
            "Driver1": d1, "Driver2": d2,
            "Race_D1": race_d1, "Race_D2": race_d2,
            "Quali_D1": quali_d1, "Quali_D2": quali_d2,
            "Points_D1": int(g[g["Driver"] == d1]["Points"].sum()),
            "Points_D2": int(g[g["Driver"] == d2]["Points"].sum()),
        })
    return pd.DataFrame(rows)


def plot_teammate_battles(battles: pd.DataFrame, session=None,
                          assets_path: str = "assets") -> plt.Figure:
    """Diverging bars: race head-to-head wins per team (D1 left, D2 right)."""
    fig, ax = plt.subplots(figsize=(12, max(6, len(battles) * 0.7)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")

    for i, (_, row) in enumerate(battles.iterrows()):
        try:
            color = fastf1.plotting.get_team_color(row["Team"], session=session)
        except Exception:
            color = "#888"
        ax.barh(i, -row["Race_D1"], color=color, alpha=0.9, height=0.6)
        ax.barh(i, row["Race_D2"], color=color, alpha=0.5, height=0.6)
        ax.text(-row["Race_D1"] - 0.15, i, f"{row['Driver1']} {row['Race_D1']}",
                ha="right", va="center", color="white", fontsize=9)
        ax.text(row["Race_D2"] + 0.15, i, f"{row['Race_D2']} {row['Driver2']}",
                ha="left", va="center", color="white", fontsize=9)

    ax.axvline(0, color="white", linewidth=1)
    ax.set_yticks([])
    ax.set_xlabel("Race head-to-head (finishes ahead of teammate)",
                  color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    lim = max(battles[["Race_D1", "Race_D2"]].max().max(), 1) + 2
    ax.set_xlim(-lim, lim)
    year = "" if battles.empty else ""
    ax.set_title("Teammate Battle — Race Head-to-Head",
                 color="white", fontsize=14, fontweight="bold", pad=12)

    plt.tight_layout()
    save_fig(fig, "S2_teammate_battles.png", assets_path)
    return fig
