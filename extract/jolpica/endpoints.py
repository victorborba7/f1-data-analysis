"""
One extractor per Jolpica/Ergast endpoint. Each returns a tidy ``pandas``
DataFrame with raw-but-flattened columns — no business logic, no surrogate keys.
That modelling happens downstream in dbt. Foreign references are kept as their
natural Ergast ids (``driverId``, ``constructorId``, ``circuitId``).

Heavier, per-race collections (results, qualifying, pit stops, standings) are
pulled season-by-season so a backfill is naturally chunked and resumable.
"""
from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .client import JolpicaClient


# ---------------------------------------------------------------------------
# Reference dimensions (small, history-wide single collections)
# ---------------------------------------------------------------------------

def pull_seasons(client: JolpicaClient) -> pd.DataFrame:
    rows = [{"season": int(s["season"]), "url": s.get("url")}
            for s in client.paginate("seasons", "SeasonTable", "Seasons")]
    return pd.DataFrame(rows)


def pull_circuits(client: JolpicaClient) -> pd.DataFrame:
    rows = []
    for c in client.paginate("circuits", "CircuitTable", "Circuits"):
        loc = c.get("Location", {})
        rows.append({
            "circuit_id": c["circuitId"],
            "circuit_name": c.get("circuitName"),
            "locality": loc.get("locality"),
            "country": loc.get("country"),
            "lat": _to_float(loc.get("lat")),
            "lng": _to_float(loc.get("long")),
            "url": c.get("url"),
        })
    return pd.DataFrame(rows)


def pull_drivers(client: JolpicaClient) -> pd.DataFrame:
    rows = []
    for d in client.paginate("drivers", "DriverTable", "Drivers"):
        rows.append({
            "driver_id": d["driverId"],
            "permanent_number": _to_int(d.get("permanentNumber")),
            "code": d.get("code"),
            "given_name": d.get("givenName"),
            "family_name": d.get("familyName"),
            "date_of_birth": d.get("dateOfBirth"),
            "nationality": d.get("nationality"),
            "url": d.get("url"),
        })
    return pd.DataFrame(rows)


def pull_constructors(client: JolpicaClient) -> pd.DataFrame:
    rows = [{
        "constructor_id": c["constructorId"],
        "name": c.get("name"),
        "nationality": c.get("nationality"),
        "url": c.get("url"),
    } for c in client.paginate("constructors", "ConstructorTable", "Constructors")]
    return pd.DataFrame(rows)


def pull_status(client: JolpicaClient) -> pd.DataFrame:
    rows = [{
        "status_id": _to_int(s["statusId"]),
        "status": s.get("status"),
        "count": _to_int(s.get("count")),
    } for s in client.paginate("status", "StatusTable", "Status")]
    return pd.DataFrame(rows)


def pull_races(client: JolpicaClient) -> pd.DataFrame:
    """Every race in history (the event dimension backbone)."""
    rows = []
    for r in client.paginate("races", "RaceTable", "Races"):
        rows.append({
            "season": int(r["season"]),
            "round": int(r["round"]),
            "race_name": r.get("raceName"),
            "circuit_id": r.get("Circuit", {}).get("circuitId"),
            "date": r.get("date"),
            "time": r.get("time"),
            "url": r.get("url"),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Facts (pulled season-by-season)
# ---------------------------------------------------------------------------

def pull_results(client: JolpicaClient, seasons: Iterable[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for race in client.paginate(f"{season}/results", "RaceTable", "Races"):
            base = {"season": int(race["season"]), "round": int(race["round"])}
            for res in race.get("Results", []):
                fl = res.get("FastestLap", {})
                rows.append({
                    **base,
                    "driver_id": res["Driver"]["driverId"],
                    "constructor_id": res["Constructor"]["constructorId"],
                    "car_number": _to_int(res.get("number")),
                    "grid": _to_int(res.get("grid")),
                    "position": _to_int(res.get("position")),
                    "position_text": res.get("positionText"),
                    "points": _to_float(res.get("points")),
                    "laps": _to_int(res.get("laps")),
                    "status": res.get("status"),
                    "time_millis": _to_int(res.get("Time", {}).get("millis")),
                    "fastest_lap_rank": _to_int(fl.get("rank")),
                    "fastest_lap_number": _to_int(fl.get("lap")),
                    "fastest_lap_time": fl.get("Time", {}).get("time"),
                })
    return pd.DataFrame(rows)


def pull_qualifying(client: JolpicaClient, seasons: Iterable[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for race in client.paginate(f"{season}/qualifying", "RaceTable", "Races"):
            base = {"season": int(race["season"]), "round": int(race["round"])}
            for q in race.get("QualifyingResults", []):
                rows.append({
                    **base,
                    "driver_id": q["Driver"]["driverId"],
                    "constructor_id": q["Constructor"]["constructorId"],
                    "position": _to_int(q.get("position")),
                    "q1": q.get("Q1"),
                    "q2": q.get("Q2"),
                    "q3": q.get("Q3"),
                })
    return pd.DataFrame(rows)


def pull_pit_stops(client: JolpicaClient, races: pd.DataFrame,
                   seasons: Iterable[int]) -> pd.DataFrame:
    """Pit stops are per-race endpoints and only exist from 2011 onward."""
    season_set = set(seasons)
    target = races[races["season"].isin(season_set)][["season", "round"]]
    rows = []
    for _, ev in target.iterrows():
        season, rnd = int(ev["season"]), int(ev["round"])
        for race in client.paginate(f"{season}/{rnd}/pitstops", "RaceTable", "Races"):
            for ps in race.get("PitStops", []):
                rows.append({
                    "season": season,
                    "round": rnd,
                    "driver_id": ps.get("driverId"),
                    "stop": _to_int(ps.get("stop")),
                    "lap": _to_int(ps.get("lap")),
                    "time_of_day": ps.get("time"),
                    "duration_s": _to_float(ps.get("duration")),
                })
    return pd.DataFrame(rows)


def pull_driver_standings(client: JolpicaClient, seasons: Iterable[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for sl in client.paginate(f"{season}/driverStandings",
                                  "StandingsTable", "StandingsLists"):
            rnd = _to_int(sl.get("round"))
            for s in sl.get("DriverStandings", []):
                cons = s.get("Constructors", [{}])
                rows.append({
                    "season": int(season),
                    "round": rnd,
                    "driver_id": s["Driver"]["driverId"],
                    "constructor_id": cons[-1].get("constructorId") if cons else None,
                    "position": _to_int(s.get("position")),
                    "points": _to_float(s.get("points")),
                    "wins": _to_int(s.get("wins")),
                })
    return pd.DataFrame(rows)


def pull_constructor_standings(client: JolpicaClient, seasons: Iterable[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for sl in client.paginate(f"{season}/constructorStandings",
                                  "StandingsTable", "StandingsLists"):
            rnd = _to_int(sl.get("round"))
            for s in sl.get("ConstructorStandings", []):
                rows.append({
                    "season": int(season),
                    "round": rnd,
                    "constructor_id": s["Constructor"]["constructorId"],
                    "position": _to_int(s.get("position")),
                    "points": _to_float(s.get("points")),
                    "wins": _to_int(s.get("wins")),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
