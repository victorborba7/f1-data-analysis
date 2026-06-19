"""
Reusable helpers for F1 data analysis with FastF1.

Colours and the chart theme come from the design system (single source of
truth: design/tokens.yml). Edit there and run `python design/build_tokens.py`
to regenerate; never hard-code a hex in this module.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.collections import LineCollection
import fastf1
import fastf1.plotting
import fastf1.utils

# Make the repo root importable so `design.generated.tokens` resolves even when
# this module is imported from a notebook deep in analysis/.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from design.generated import tokens as T  # noqa: E402

# Re-exported so `from utils.f1_helpers import COMPOUND_COLORS` still works.
COMPOUND_COLORS = T.COMPOUND_COLORS


def setup(cache_path: str = "content/f1_cache") -> None:
    os.makedirs(cache_path, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path)
    fastf1.plotting.setup_mpl(color_scheme="fastf1")
    plt.style.use(T.MPLSTYLE)  # F1 design-system chart theme (over fastf1's)


def ensure_assets_dir(assets_path: str = "assets") -> str:
    os.makedirs(assets_path, exist_ok=True)
    return assets_path


def save_fig(fig: plt.Figure, filename: str, assets_path: str = "assets", dpi: int = T.FIG_DPI) -> str:
    path = os.path.join(assets_path, filename)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved → {path}")
    return path


# ---------------------------------------------------------------------------
# Race results
# ---------------------------------------------------------------------------

def get_race_results(session) -> pd.DataFrame:
    results = session.results[
        ["Position", "FullName", "TeamName", "Points", "Status", "Time"]
    ].copy()
    results["Position"] = pd.to_numeric(results["Position"], errors="coerce")
    return results.sort_values("Position").reset_index(drop=True)


def plot_race_results(session, assets_path: str = "assets") -> plt.Figure:
    results = get_race_results(session)
    top10 = results.head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    colors = [
        fastf1.plotting.get_team_color(team, session=session)
        for team in top10["TeamName"]
    ]
    bars = ax.barh(range(len(top10)), top10["Points"], color=colors)

    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(
        [f"P{int(r['Position'])} · {r['FullName']}" for _, r in top10.iterrows()],
        color="white", fontsize=10
    )
    ax.invert_yaxis()
    ax.set_xlabel("Points", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Race Results (Top 10)",
        color="white", fontsize=14, fontweight="bold", pad=12
    )

    for bar, pts in zip(bars, top10["Points"]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                str(int(pts)), va="center", color="white", fontsize=9)

    plt.tight_layout()
    save_fig(fig, "01_race_results.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Lap time evolution
# ---------------------------------------------------------------------------

def plot_lap_times(session, drivers: list[str] | None = None,
                   assets_path: str = "assets") -> plt.Figure:
    laps = session.laps.pick_quicklaps()

    if drivers is None:
        results = get_race_results(session)
        drivers = results["FullName"].head(5).tolist()
        driver_abbrs = [
            session.results[session.results["FullName"] == d]["Abbreviation"].values[0]
            for d in drivers
        ]
    else:
        driver_abbrs = drivers

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    for drv in driver_abbrs:
        drv_laps = laps.pick_driver(drv)
        if drv_laps.empty:
            continue
        color = fastf1.plotting.get_driver_color(drv, session=session)
        lap_times_s = drv_laps["LapTime"].dt.total_seconds()
        ax.plot(drv_laps["LapNumber"], lap_times_s, color=color, label=drv, linewidth=1.6)

    ax.set_xlabel("Lap", color="white", fontsize=11)
    ax.set_ylabel("Lap Time (s)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
    ax.grid(alpha=0.15, color="white")
    ax.legend(facecolor=T.SURFACE_RAISED, labelcolor="white", fontsize=9)
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Lap Time Evolution",
        color="white", fontsize=14, fontweight="bold", pad=12
    )

    plt.tight_layout()
    save_fig(fig, "02_lap_time_evolution.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Tyre strategy
# ---------------------------------------------------------------------------

def plot_tyre_strategy(session, assets_path: str = "assets") -> plt.Figure:
    laps = session.laps
    results = get_race_results(session)
    drivers = results["FullName"].head(10).tolist()
    abbrs = [
        session.results[session.results["FullName"] == d]["Abbreviation"].values[0]
        for d in drivers
    ]

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    for i, drv in enumerate(abbrs):
        drv_laps = laps.pick_driver(drv)[["LapNumber", "Compound", "Stint"]].dropna()
        for _, row in drv_laps.iterrows():
            color = COMPOUND_COLORS.get(row["Compound"], COMPOUND_COLORS["UNKNOWN"])
            ax.barh(i, 1, left=row["LapNumber"] - 1, color=color, height=0.6, edgecolor="none")

    ax.set_yticks(range(len(abbrs)))
    ax.set_yticklabels(abbrs, color="white", fontsize=10)
    ax.set_xlabel("Lap", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Tyre Strategy",
        color="white", fontsize=14, fontweight="bold", pad=12
    )

    legend_patches = [
        mpatches.Patch(color=v, label=k) for k, v in COMPOUND_COLORS.items() if k != "UNKNOWN"
    ]
    ax.legend(handles=legend_patches, facecolor=T.SURFACE_RAISED, labelcolor="white",
              fontsize=9, loc="lower right")

    plt.tight_layout()
    save_fig(fig, "03_tyre_strategy.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Telemetry comparison
# ---------------------------------------------------------------------------

def plot_telemetry(session, driver1: str, driver2: str,
                   assets_path: str = "assets") -> plt.Figure:
    laps = session.laps

    lap1 = laps.pick_driver(driver1).pick_fastest()
    lap2 = laps.pick_driver(driver2).pick_fastest()

    tel1 = lap1.get_telemetry().add_distance()
    tel2 = lap2.get_telemetry().add_distance()

    color1 = fastf1.plotting.get_driver_color(driver1, session=session)
    color2 = fastf1.plotting.get_driver_color(driver2, session=session)

    channels = [
        ("Speed", "Speed (km/h)", (0, 360)),
        ("Throttle", "Throttle (%)", (0, 105)),
        ("Brake", "Brake", (-0.1, 1.1)),
        ("nGear", "Gear", (0, 9)),
    ]

    fig, axes = plt.subplots(len(channels), 1, figsize=(14, 12), sharex=True)
    fig.patch.set_facecolor(T.SURFACE_BASE)

    t1_s = lap1["LapTime"].total_seconds()
    t2_s = lap2["LapTime"].total_seconds()
    delta = t1_s - t2_s
    sign = "+" if delta > 0 else ""
    fig.suptitle(
        f"{session.event['EventName']} {session.event.year} — {driver1} vs {driver2} Fastest Lap\n"
        f"{driver1}: {t1_s:.3f}s  |  {driver2}: {t2_s:.3f}s  |  Δ {sign}{delta:.3f}s",
        color="white", fontsize=13, fontweight="bold", y=0.99
    )

    for ax, (ch, ylabel, ylim) in zip(axes, channels):
        ax.set_facecolor(T.SURFACE_BASE)
        if ch in tel1.columns:
            ax.plot(tel1["Distance"], tel1[ch], color=color1, label=driver1, linewidth=1.4)
        if ch in tel2.columns:
            ax.plot(tel2["Distance"], tel2[ch], color=color2, label=driver2,
                    linewidth=1.4, linestyle="--")
        ax.set_ylabel(ylabel, color="white", fontsize=9)
        ax.set_ylim(ylim)
        ax.tick_params(colors="white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
        ax.grid(alpha=0.12, color="white")

    axes[0].legend(facecolor=T.SURFACE_RAISED, labelcolor="white", fontsize=9, loc="upper right")
    axes[-1].set_xlabel("Distance (m)", color="white", fontsize=11)
    axes[-1].tick_params(axis="x", colors="white")

    plt.tight_layout()
    save_fig(fig, f"04_telemetry_{driver1}_vs_{driver2}.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Qualifying
# ---------------------------------------------------------------------------

def get_qualifying_times(session) -> pd.DataFrame:
    """Best lap time per driver across all Q segments."""
    records = []
    for _, driver in session.results.iterrows():
        abbr = driver["Abbreviation"]
        drv_laps = session.laps.pick_driver(abbr).pick_quicklaps()
        if drv_laps.empty:
            continue
        fastest = drv_laps.pick_fastest()
        records.append({
            "Driver": abbr,
            "FullName": driver["FullName"],
            "Team": driver["TeamName"],
            "GridPosition": pd.to_numeric(driver.get("Position", np.nan), errors="coerce"),
            "LapTime": fastest["LapTime"].total_seconds(),
        })
    df = pd.DataFrame(records).sort_values("LapTime").reset_index(drop=True)
    df["Delta"] = df["LapTime"] - df["LapTime"].iloc[0]
    return df


def plot_qualifying_times(session, top_n: int = 15, assets_path: str = "assets") -> plt.Figure:
    df = get_qualifying_times(session).head(top_n)
    pole_time = df["LapTime"].iloc[0]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    colors = [fastf1.plotting.get_team_color(t, session=session) for t in df["Team"]]
    bars = ax.barh(range(len(df)), df["Delta"], color=colors, height=0.65)

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(
        [f"P{int(r['GridPosition'])}  {r['Driver']}" for _, r in df.iterrows()],
        color="white", fontsize=10
    )
    ax.invert_yaxis()
    ax.set_xlabel("Gap to Pole (s)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.grid(axis="x", alpha=0.15, color="white")

    pole_min = int(pole_time // 60)
    pole_sec = pole_time % 60
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Qualifying Times\n"
        f"Pole: {df.iloc[0]['Driver']}  {pole_min}:{pole_sec:06.3f}",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    for bar, (_, row) in zip(bars, df.iterrows()):
        label = "POLE" if row["Delta"] == 0 else f"+{row['Delta']:.3f}s"
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                label, va="center", color="white", fontsize=8)

    plt.tight_layout()
    save_fig(fig, "Q1_qualifying_times.png", assets_path)
    return fig


def plot_sector_times(session, top_n: int = 10, assets_path: str = "assets") -> plt.Figure:
    """Compare best sector times per driver for the top N qualifiers."""
    quali_df = get_qualifying_times(session).head(top_n)
    drivers = quali_df["Driver"].tolist()

    sector_data = []
    for drv in drivers:
        drv_laps = session.laps.pick_driver(drv).pick_quicklaps()
        if drv_laps.empty:
            continue
        fastest = drv_laps.pick_fastest()
        sector_data.append({
            "Driver": drv,
            "Team": quali_df[quali_df["Driver"] == drv]["Team"].values[0],
            "S1": fastest["Sector1Time"].total_seconds() if pd.notna(fastest["Sector1Time"]) else np.nan,
            "S2": fastest["Sector2Time"].total_seconds() if pd.notna(fastest["Sector2Time"]) else np.nan,
            "S3": fastest["Sector3Time"].total_seconds() if pd.notna(fastest["Sector3Time"]) else np.nan,
        })

    df = pd.DataFrame(sector_data)
    sectors = ["S1", "S2", "S3"]
    sector_labels = ["Sector 1", "Sector 2", "Sector 3"]
    best = {s: df[s].min() for s in sectors}

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    fig.suptitle(
        f"{session.event['EventName']} {session.event.year} — Best Sector Times (Top {top_n})",
        color="white", fontsize=13, fontweight="bold"
    )

    for ax, s, label in zip(axes, sectors, sector_labels):
        ax.set_facecolor(T.SURFACE_BASE)
        df_s = df[["Driver", "Team", s]].dropna().sort_values(s)
        colors = [fastf1.plotting.get_team_color(t, session=session) for t in df_s["Team"]]
        df_s["Delta"] = df_s[s] - best[s]
        bars = ax.barh(range(len(df_s)), df_s["Delta"], color=colors, height=0.65)
        ax.set_yticks(range(len(df_s)))
        ax.set_yticklabels(df_s["Driver"], color="white", fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Gap (s)", color="white", fontsize=9)
        ax.set_title(label, color="white", fontsize=11, fontweight="bold")
        ax.tick_params(colors="white")
        ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
        ax.grid(axis="x", alpha=0.15, color="white")
        for bar, (_, row) in zip(bars, df_s.iterrows()):
            label_txt = "BEST" if row["Delta"] == 0 else f"+{row['Delta']:.3f}"
            ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                    label_txt, va="center", color="white", fontsize=7)

    plt.tight_layout()
    save_fig(fig, "Q2_sector_times.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Weekend summary — grid vs finish
# ---------------------------------------------------------------------------

def plot_positions_gained(race_session, assets_path: str = "assets") -> plt.Figure:
    """Slope chart: grid position → race finish, highlighting biggest movers."""
    results = race_session.results.copy()
    results["GridPosition"] = pd.to_numeric(results["GridPosition"], errors="coerce")
    results["Position"] = pd.to_numeric(results["Position"], errors="coerce")
    results = results.dropna(subset=["GridPosition", "Position"])
    results["Gained"] = results["GridPosition"] - results["Position"]
    results = results.sort_values("GridPosition").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 9))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    for _, row in results.iterrows():
        color = fastf1.plotting.get_team_color(row["TeamName"], session=race_session)
        gained = row["Gained"]
        lw = 2.0
        ax.plot([0, 1], [row["GridPosition"], row["Position"]], color=color, linewidth=lw, alpha=0.85)

        label_left = f"P{int(row['GridPosition'])} {row['Abbreviation']}"
        label_right = f"{row['Abbreviation']} P{int(row['Position'])}"
        gained_str = f" (+{int(gained)})" if gained > 0 else (f" ({int(gained)})" if gained < 0 else "")

        ax.text(-0.02, row["GridPosition"], label_left, ha="right", va="center",
                color="white", fontsize=8)
        ax.text(1.02, row["Position"], label_right + gained_str, ha="left", va="center",
                color=(T.SEMANTIC_POSITIVE if gained > 0 else T.SEMANTIC_NEGATIVE if gained < 0 else "white"),
                fontsize=8)

    ax.set_xlim(-0.3, 1.3)
    max_pos = int(results[["GridPosition", "Position"]].max().max())
    ax.set_ylim(max_pos + 0.5, 0.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["GRID", "FINISH"], color="white", fontsize=12, fontweight="bold")
    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.set_title(
        f"{race_session.event['EventName']} {race_session.event.year} — Positions Gained / Lost",
        color="white", fontsize=13, fontweight="bold", pad=14
    )

    gain_line = mlines.Line2D([], [], color=T.SEMANTIC_POSITIVE, label="Positions gained")
    loss_line = mlines.Line2D([], [], color=T.SEMANTIC_NEGATIVE, label="Positions lost")
    ax.legend(handles=[gain_line, loss_line], facecolor=T.SURFACE_RAISED, labelcolor="white",
              fontsize=9, loc="lower center")

    plt.tight_layout()
    save_fig(fig, "W1_positions_gained.png", assets_path)
    return fig


def plot_pace_comparison(sessions: dict, drivers: list[str],
                         assets_path: str = "assets") -> plt.Figure:
    """
    Compare median lap pace across multiple sessions for a set of drivers.
    sessions = {'Q': quali_session, 'R': race_session} (or add 'S' for Sprint)
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    session_labels = list(sessions.keys())
    x = np.arange(len(session_labels))
    width = 0.8 / max(len(drivers), 1)

    for i, drv in enumerate(drivers):
        medians = []
        ref_session = next(iter(sessions.values()))
        color = fastf1.plotting.get_driver_color(drv, session=ref_session)
        for sess in sessions.values():
            drv_laps = sess.laps.pick_driver(drv).pick_quicklaps()
            medians.append(drv_laps["LapTime"].dt.total_seconds().median() if not drv_laps.empty else np.nan)
        offset = (i - len(drivers) / 2 + 0.5) * width
        ax.bar(x + offset, medians, width=width * 0.9, color=color, label=drv)

    ax.set_xticks(x)
    ax.set_xticklabels(session_labels, color="white", fontsize=12)
    ax.set_ylabel("Median Lap Time (s)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
    ax.grid(axis="y", alpha=0.15, color="white")
    ax.legend(facecolor=T.SURFACE_RAISED, labelcolor="white", fontsize=9)
    ax.set_title(
        f"{ref_session.event['EventName']} {ref_session.event.year} — Pace Across Sessions",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    plt.tight_layout()
    save_fig(fig, "W2_pace_comparison.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Corner-by-corner time loss (delta-time analysis)
# ---------------------------------------------------------------------------

def get_lap(session, driver: str, lap_selector="fastest"):
    """
    Fetch a single lap.
    lap_selector: 'fastest' (default) or an integer lap number.
    """
    drv_laps = session.laps.pick_driver(driver)
    if lap_selector == "fastest":
        return drv_laps.pick_fastest()
    return drv_laps[drv_laps["LapNumber"] == int(lap_selector)].iloc[0]


def _corner_label(row) -> str:
    letter = str(row["Letter"]) if ("Letter" in row and pd.notna(row["Letter"])) else ""
    return f"T{int(row['Number'])}{letter}"


def analyze_corners(session, lap_ref, lap_comp) -> dict:
    """
    Delta-time analysis between two laps, broken down per corner.

    REFERENCE = the benchmark (target) lap.
    COMPARE   = the lap being analysed.

    The delta curve is negative where COMPARE is ahead of REFERENCE.
    Where it RISES, COMPARE is losing time. We split the track into
    one segment per corner (cut at the midpoint between corners) and
    measure how much the delta changes inside each segment.

    Returns a dict with:
      df        — per-corner DataFrame (Corner, Distance, TimeLost, Cumulative)
      dist      — reference distance axis (m)
      delta     — delta-time array aligned to dist (s)
      ref, comp — reference / compare telemetry frames
      ref_name, comp_name — driver abbreviations
    """
    delta, ref, comp = fastf1.utils.delta_time(lap_ref, lap_comp)
    dist = ref["Distance"].to_numpy()
    delta_arr = np.asarray(delta, dtype=float)

    corners = session.get_circuit_info().corners.copy()
    corners = corners.sort_values("Distance").reset_index(drop=True)
    cd = corners["Distance"].to_numpy()

    # segment boundaries: start, midpoints between corners, end
    bounds = np.empty(len(cd) + 1)
    bounds[0] = dist.min()
    bounds[-1] = dist.max()
    bounds[1:-1] = (cd[:-1] + cd[1:]) / 2.0

    rows = []
    for i, corner in corners.iterrows():
        d0, d1 = bounds[i], bounds[i + 1]
        delta0 = np.interp(d0, dist, delta_arr)
        delta1 = np.interp(d1, dist, delta_arr)
        rows.append({
            "Corner": _corner_label(corner),
            "Distance": float(corner["Distance"]),
            "TimeLost": float(delta1 - delta0),  # +ve = COMPARE lost time here
        })

    df = pd.DataFrame(rows)
    df["Cumulative"] = df["TimeLost"].cumsum()

    return {
        "df": df,
        "dist": dist,
        "delta": delta_arr,
        "ref": ref,
        "comp": comp,
        "ref_name": lap_ref["Driver"],
        "comp_name": lap_comp["Driver"],
    }


def plot_delta_trace(session, analysis: dict, lap_ref, lap_comp,
                     assets_path: str = "assets") -> plt.Figure:
    """Speed traces + delta-time curve with corner markers."""
    ref, comp = analysis["ref"], analysis["comp"]
    dist, delta = analysis["dist"], analysis["delta"]
    ref_name, comp_name = analysis["ref_name"], analysis["comp_name"]

    ref_color = T.SEMANTIC_NEUTRAL  # benchmark = neutral grey
    comp_color = fastf1.plotting.get_driver_color(comp_name, session=session)
    if comp_color.lower() in (T.SEMANTIC_NEUTRAL,):
        comp_color = T.SEMANTIC_NEGATIVE

    corners = session.get_circuit_info().corners.sort_values("Distance")

    fig, (ax_s, ax_d) = plt.subplots(
        2, 1, figsize=(15, 9), sharex=True,
        gridspec_kw={"height_ratios": [2, 1.4], "hspace": 0.08}
    )
    fig.patch.set_facecolor(T.SURFACE_BASE)

    t_ref = lap_ref["LapTime"].total_seconds()
    t_comp = lap_comp["LapTime"].total_seconds()
    gap = t_comp - t_ref
    fig.suptitle(
        f"{session.event['EventName']} {session.event.year} — Corner Time Loss\n"
        f"REF {ref_name} {t_ref:.3f}s   vs   {comp_name} {t_comp:.3f}s   "
        f"(total gap {gap:+.3f}s)",
        color="white", fontsize=13, fontweight="bold", y=0.98
    )

    # --- Speed traces ---
    ax_s.set_facecolor(T.SURFACE_BASE)
    ax_s.plot(ref["Distance"], ref["Speed"], color=ref_color, linewidth=1.6,
              label=f"{ref_name} (ref)")
    ax_s.plot(comp["Distance"], comp["Speed"], color=comp_color, linewidth=1.6,
              linestyle="--", label=f"{comp_name}")
    ax_s.set_ylabel("Speed (km/h)", color="white", fontsize=11)
    ax_s.legend(facecolor=T.SURFACE_RAISED, labelcolor="white", fontsize=9, loc="lower right")

    # --- Delta curve ---
    ax_d.set_facecolor(T.SURFACE_BASE)
    ax_d.plot(dist, delta, color="white", linewidth=1.6)
    ax_d.axhline(0, color=T.AXIS_ZERO, linewidth=0.8)
    # shade where COMPARE is losing (delta rising) vs gaining
    ax_d.fill_between(dist, delta, 0, where=(delta > 0), color=T.SEMANTIC_NEGATIVE, alpha=0.25,
                      interpolate=True)
    ax_d.fill_between(dist, delta, 0, where=(delta <= 0), color=T.SEMANTIC_POSITIVE, alpha=0.25,
                      interpolate=True)
    ax_d.set_ylabel(f"Δt (s)\n← {comp_name} ahead | behind →", color="white", fontsize=10)
    ax_d.set_xlabel("Distance (m)", color="white", fontsize=11)

    # --- Corner markers on both axes ---
    for ax in (ax_s, ax_d):
        for _, c in corners.iterrows():
            ax.axvline(c["Distance"], color=T.AXIS_MARKER, linewidth=0.6, linestyle=":", zorder=0)
        ax.tick_params(colors="white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
        ax.grid(alpha=0.10, color="white")

    ymax = ax_s.get_ylim()[1]
    for _, c in corners.iterrows():
        ax_s.text(c["Distance"], ymax * 0.99, _corner_label(c),
                  color=T.TEXT_FAINT, fontsize=7, ha="center", va="top", rotation=90)

    save_fig(fig, f"C1_delta_trace_{ref_name}_vs_{comp_name}.png", assets_path)
    return fig


def plot_corner_breakdown(session, analysis: dict,
                          assets_path: str = "assets") -> plt.Figure:
    """Horizontal bars: time lost (red) / gained (green) per corner, in track order."""
    df = analysis["df"]
    ref_name, comp_name = analysis["ref_name"], analysis["comp_name"]

    fig, ax = plt.subplots(figsize=(11, max(6, len(df) * 0.4)))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    colors = [T.SEMANTIC_NEGATIVE if v > 0 else T.SEMANTIC_POSITIVE for v in df["TimeLost"]]
    ax.barh(range(len(df)), df["TimeLost"], color=colors, height=0.7)

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["Corner"], color="white", fontsize=9)
    ax.invert_yaxis()
    ax.axvline(0, color=T.AXIS_ZERO, linewidth=0.8)
    ax.set_xlabel(f"Time lost by {comp_name} vs {ref_name}  (s)   "
                  f"→ losing | gaining ←", color="white", fontsize=10)
    ax.tick_params(colors="white")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.grid(axis="x", alpha=0.15, color="white")

    total = df["TimeLost"].sum()
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — "
        f"Corner-by-Corner Time Loss\n{comp_name} vs {ref_name}  "
        f"(net {total:+.3f}s)",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    for i, v in enumerate(df["TimeLost"]):
        ax.text(v + (0.003 if v >= 0 else -0.003), i, f"{v:+.3f}",
                va="center", ha="left" if v >= 0 else "right",
                color="white", fontsize=7)

    plt.tight_layout()
    save_fig(fig, f"C2_corner_breakdown_{ref_name}_vs_{comp_name}.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Race pace distribution (box plot)
# ---------------------------------------------------------------------------

def plot_race_pace(session, top_n: int = 10, assets_path: str = "assets") -> plt.Figure:
    """
    Box plot of clean lap times per driver — reveals true race pace with
    in/out laps and traffic-affected laps removed. Drivers ordered by median.
    """
    laps = session.laps.pick_quicklaps().copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()

    results = get_race_results(session)
    abbrs = [
        session.results[session.results["FullName"] == d]["Abbreviation"].values[0]
        for d in results["FullName"].head(top_n)
    ]

    data, labels, colors, medians = [], [], [], []
    for drv in abbrs:
        vals = laps[laps["Driver"] == drv]["LapTimeSeconds"].dropna().to_numpy()
        if len(vals) < 3:
            continue
        data.append(vals)
        labels.append(drv)
        colors.append(fastf1.plotting.get_driver_color(drv, session=session))
        medians.append(np.median(vals))

    order = np.argsort(medians)  # fastest median first
    data = [data[i] for i in order]
    labels = [labels[i] for i in order]
    colors = [colors[i] for i in order]

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    bp = ax.boxplot(data, vert=False, patch_artist=True, showfliers=False,
                    widths=0.6)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
        patch.set_edgecolor("white")
    for element in ("whiskers", "caps", "medians"):
        for item in bp[element]:
            item.set_color("white")

    ax.set_yticks(range(1, len(labels) + 1))
    ax.set_yticklabels(labels, color="white", fontsize=10)
    ax.invert_yaxis()  # fastest at top
    ax.set_xlabel("Lap Time (s)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
    ax.grid(axis="x", alpha=0.15, color="white")
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Race Pace Distribution\n"
        f"(clean laps only · ordered by median)",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    plt.tight_layout()
    save_fig(fig, "P1_race_pace.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Tyre degradation model
# ---------------------------------------------------------------------------

def tyre_degradation_summary(session, min_laps: int = 8) -> pd.DataFrame:
    """
    Linear regression of lap time vs tyre age per compound.
    Slope (s/lap) = degradation rate. Note: not fuel-corrected, so early
    in a stint fuel burn can offset tyre wear — read the slope as a trend.
    """
    laps = session.laps.pick_quicklaps().copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()

    rows = []
    for comp in COMPOUND_COLORS:
        if comp == "UNKNOWN":
            continue
        sub = laps[laps["Compound"] == comp]
        x = sub["TyreLife"].to_numpy(dtype=float)
        y = sub["LapTimeSeconds"].to_numpy(dtype=float)
        mask = ~np.isnan(x) & ~np.isnan(y)
        x, y = x[mask], y[mask]
        if len(x) < min_laps:
            continue
        slope, intercept = np.polyfit(x, y, 1)
        rows.append({
            "Compound": comp,
            "Laps": len(x),
            "DegRate_s_per_lap": round(float(slope), 4),
            "BaseLap_s": round(float(intercept), 3),
        })
    return pd.DataFrame(rows)


def plot_tyre_degradation(session, min_laps: int = 8,
                          assets_path: str = "assets") -> plt.Figure:
    laps = session.laps.pick_quicklaps().copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    for comp, color in COMPOUND_COLORS.items():
        if comp == "UNKNOWN":
            continue
        sub = laps[laps["Compound"] == comp]
        x = sub["TyreLife"].to_numpy(dtype=float)
        y = sub["LapTimeSeconds"].to_numpy(dtype=float)
        mask = ~np.isnan(x) & ~np.isnan(y)
        x, y = x[mask], y[mask]
        if len(x) < min_laps:
            continue
        ax.scatter(x, y, color=color, alpha=0.35, s=14, edgecolors="none")
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, slope * xs + intercept, color=color, linewidth=2.4,
                label=f"{comp}: {slope:+.3f} s/lap")

    ax.set_xlabel("Tyre Age (laps)", color="white", fontsize=11)
    ax.set_ylabel("Lap Time (s)", color="white", fontsize=11)
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(T.AXIS_SPINE)
    ax.grid(alpha=0.15, color="white")
    ax.legend(facecolor=T.SURFACE_RAISED, labelcolor="white", fontsize=10, title="Degradation")
    ax.get_legend().get_title().set_color("white")
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Tyre Degradation by Compound",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    plt.tight_layout()
    save_fig(fig, "P2_tyre_degradation.png", assets_path)
    return fig


# ---------------------------------------------------------------------------
# Track dominance map
# ---------------------------------------------------------------------------

def _rotate_xy(xy: np.ndarray, angle: float) -> np.ndarray:
    rot = np.array([[np.cos(angle), np.sin(angle)],
                    [-np.sin(angle), np.cos(angle)]])
    return xy @ rot


def plot_track_dominance(session, drivers: list[str] | None = None,
                         n_minisectors: int = 25,
                         assets_path: str = "assets") -> plt.Figure:
    """
    Colour the circuit by which driver is fastest in each mini-sector,
    based on each driver's fastest lap. 2-3 drivers reads best.
    """
    if drivers is None:
        # fastest 3 drivers by their single best lap
        best = (session.laps.pick_quicklaps()
                .groupby("Driver")["LapTime"].min()
                .sort_values().head(3))
        drivers = best.index.tolist()

    frames = []
    for drv in drivers:
        lap = session.laps.pick_driver(drv).pick_fastest()
        tel = lap.get_telemetry().add_distance()
        tel = tel[["Distance", "Speed", "X", "Y"]].copy()
        tel["Driver"] = drv
        frames.append(tel)

    tel_all = pd.concat(frames, ignore_index=True)
    total = tel_all["Distance"].max()
    seg_len = total / n_minisectors
    tel_all["Minisector"] = (tel_all["Distance"] // seg_len).astype(int)

    # fastest driver per mini-sector (by average speed)
    avg = tel_all.groupby(["Minisector", "Driver"])["Speed"].mean().reset_index()
    fastest = avg.loc[avg.groupby("Minisector")["Speed"].idxmax(), ["Minisector", "Driver"]]
    fastest = fastest.rename(columns={"Driver": "FastestDriver"})

    # use first driver's lap as track geometry
    ref = frames[0].copy()
    ref["Minisector"] = (ref["Distance"] // seg_len).astype(int)
    ref = ref.merge(fastest, on="Minisector", how="left")
    ref["FastestDriver"] = ref["FastestDriver"].ffill().bfill()

    xy = ref[["X", "Y"]].to_numpy(dtype=float)
    try:
        angle = session.get_circuit_info().rotation / 180 * np.pi
        xy = _rotate_xy(xy, angle)
    except Exception:
        pass

    color_map = {d: fastf1.plotting.get_driver_color(d, session=session) for d in drivers}

    points = xy.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    seg_colors = [color_map[d] for d in ref["FastestDriver"].iloc[:-1]]

    fig, ax = plt.subplots(figsize=(10, 9))
    fig.patch.set_facecolor(T.SURFACE_BASE)
    ax.set_facecolor(T.SURFACE_BASE)

    # faint full-track outline underneath
    ax.plot(xy[:, 0], xy[:, 1], color=T.SURFACE_OUTLINE, linewidth=8, zorder=1)
    lc = LineCollection(segments, colors=seg_colors, linewidth=5, zorder=2)
    ax.add_collection(lc)

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"{session.event['EventName']} {session.event.year} — Track Dominance\n"
        f"fastest driver per mini-sector",
        color="white", fontsize=13, fontweight="bold", pad=12
    )

    handles = [mlines.Line2D([], [], color=color_map[d], linewidth=4, label=d)
               for d in drivers]
    ax.legend(handles=handles, facecolor=T.SURFACE_RAISED, labelcolor="white",
              fontsize=10, loc="upper right")

    plt.tight_layout()
    save_fig(fig, "P3_track_dominance.png", assets_path)
    return fig
